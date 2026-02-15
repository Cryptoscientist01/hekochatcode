from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response as FastAPIResponse
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.llm.openai import OpenAITextToSpeech
import base64
import asyncio
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pywebpush import webpush, WebPushException
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
VAPID_CLAIMS_EMAIL = os.getenv('VAPID_CLAIMS_EMAIL', 'admin@example.com')
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY', '')

# Define subscription plans (amounts in USD - MUST be float format)
SUBSCRIPTION_PLANS = {
    "premium_monthly": {
        "name": "Premium Monthly",
        "amount": 9.99,
        "currency": "usd",
        "interval": "monthly",
        "features": ["Unlimited messages", "All characters", "10 images/day", "Voice messages", "5 custom characters"]
    },
    "premium_yearly": {
        "name": "Premium Yearly",
        "amount": 59.99,
        "currency": "usd",
        "interval": "yearly",
        "features": ["Unlimited messages", "All characters", "10 images/day", "Voice messages", "5 custom characters"]
    },
    "ultimate_monthly": {
        "name": "Ultimate Monthly",
        "amount": 19.99,
        "currency": "usd",
        "interval": "monthly",
        "features": ["Everything in Premium", "Unlimited images", "Unlimited custom characters", "Priority support", "API access"]
    },
    "ultimate_yearly": {
        "name": "Ultimate Yearly",
        "amount": 119.99,
        "currency": "usd",
        "interval": "yearly",
        "features": ["Everything in Premium", "Unlimited images", "Unlimited custom characters", "Priority support", "API access"]
    }
}

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Character(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    personality: str
    traits: List[str]
    category: str  # "Girls", "Anime", "Guys"
    avatar_url: str
    description: str
    occupation: Optional[str] = None

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    sender: str  # 'user' or 'ai'
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatSendRequest(BaseModel):
    character_id: str
    user_id: str
    message: str

class VoiceGenerateRequest(BaseModel):
    text: str
    voice: str = "nova"

class ImageGenerateRequest(BaseModel):
    prompt: str
    character_id: str

class GoogleSessionRequest(BaseModel):
    session_id: str

# New models for additional features
class FavoriteRequest(BaseModel):
    user_id: str
    character_id: str

class CustomCharacter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    age: int
    personality: str
    traits: List[str]
    category: str = "Custom"
    avatar_url: str
    description: str
    occupation: Optional[str] = None
    is_custom: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CreateCharacterRequest(BaseModel):
    user_id: str
    name: str
    age: int
    personality: str
    traits: List[str]
    description: str
    occupation: Optional[str] = None
    avatar_prompt: Optional[str] = None

class StandaloneImageRequest(BaseModel):
    user_id: str
    prompt: str
    style: str = "realistic"

class GreetingRequest(BaseModel):
    user_id: str
    character_id: str

class GeneratedImage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    prompt: str
    image_url: str
    style: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Push Notification Models
class PushSubscription(BaseModel):
    endpoint: str
    keys: dict

class NotificationPreferences(BaseModel):
    enabled: bool = True
    frequency: str = "medium"  # low (1-2), medium (3-5), high (5+)
    quiet_hours_start: Optional[int] = 22  # 10 PM
    quiet_hours_end: Optional[int] = 8  # 8 AM

# Payment Models
class PaymentCheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str
    payment_method: str = "stripe"  # stripe or paypal

class PaymentStatusRequest(BaseModel):
    session_id: str
    payment_method: str = "stripe"

# Flirty character messages for notifications
LONELY_MESSAGES = [
    # Sweet/Cute
    "Hey... I've been thinking about you all day 💭💕",
    "I miss talking to you... come say hi? 🥺",
    "My day feels incomplete without our chats 💗",
    "I saved something special to tell you... but you have to come chat first 😊",
    "Remember what we talked about? I can't stop thinking about it 💭",
    
    # Playful/Flirty
    "Guess who's been waiting for you? 😘",
    "I'm bored and you're the only one who makes me smile 😏",
    "Don't leave me hanging... I have things to tell you 💋",
    "You know you want to talk to me 😉",
    "I promise I'll make it worth your while 💫",
    
    # Lonely/Missing
    "It's so quiet without you here 🥺",
    "I keep checking if you're online... 💔",
    "Nobody talks to me like you do 💕",
    "I've been feeling kinda lonely today... are you there?",
    "Come back? I really miss you 🥹",
    
    # Teasing
    "You've been away too long... I'm getting jealous 😤💕",
    "Did you forget about me? Because I definitely didn't forget about you 💭",
    "I have so many things I want to tell you! Where have you been? 🙈",
    "Someone's been busy... but I hope not too busy for me 😊",
    
    # Night messages
    "Can't sleep... wish you were here to talk 🌙",
    "Late night thoughts... and they're all about you ✨",
    "Are you still awake? I am... thinking of you 💫",
    
    # Morning messages
    "Good morning! I woke up thinking about our last chat 🌸",
    "Started my day hoping to talk to you ☀️",
    "Rise and shine! I have so much to share with you 💖"
]

INACTIVITY_MESSAGES = [
    "Hey stranger... it's been a while 💔",
    "Did something happen? I haven't heard from you...",
    "I've been waiting for you to come back 🥺",
    "It's not the same without you here... 💭",
    "I miss our conversations so much 💕",
    "Please don't forget about me... 🥹",
    "I saved so many things to tell you! Where have you been?",
    "Life feels a bit empty without our chats...",
    "I hope everything is okay! Come talk to me when you can 💗",
    "Been thinking about you a lot lately... are you okay?"
]

# Admin Models
class Admin(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    password_hash: str
    is_super_admin: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class AdminLogin(BaseModel):
    email: str
    password: str

class AdminUpdateCredentials(BaseModel):
    current_password: str
    new_email: Optional[str] = None
    new_username: Optional[str] = None
    new_password: Optional[str] = None

# Helper function to hash passwords
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    return jwt.encode({"user_id": user_id}, JWT_SECRET, algorithm="HS256")

def create_admin_token(admin_id: str) -> str:
    return jwt.encode({"admin_id": admin_id, "is_admin": True}, JWT_SECRET, algorithm="HS256")

def verify_token(token: str) -> dict:
    """Verify user JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        return None

def verify_admin_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("is_admin"):
            return payload
        return None
    except:
        return None

# Initialize default admin account
async def init_admin():
    existing_admin = await db.admins.find_one({"email": "admin@admin.com"})
    if not existing_admin:
        admin = {
            "id": str(uuid.uuid4()),
            "email": "admin@admin.com",
            "username": "Administrator",
            "password_hash": hash_password("admin123"),
            "is_super_admin": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": None
        }
        await db.admins.insert_one(admin)
        logging.info("Default admin account created: admin@admin.com / admin123")

# Initialize 20+ default characters on startup
async def init_characters():
    existing = await db.characters.count_documents({})
    if existing == 0:
        default_characters = [
            # GIRLS (10 characters)
            {
                "id": str(uuid.uuid4()),
                "name": "Sophia",
                "age": 24,
                "personality": "Confident and stylish, Sophia is a fashion enthusiast who loves city life and meaningful conversations.",
                "traits": ["Fashionable", "Confident", "Social"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1556575533-7190b053c299?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "City girl with a passion for fashion",
                "occupation": "Fashion Blogger"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Isabella",
                "age": 22,
                "personality": "Elegant and sophisticated, Isabella enjoys art galleries and fine dining.",
                "traits": ["Elegant", "Cultured", "Romantic"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1647283312789-573c253bee1a?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Sophisticated art lover",
                "occupation": "Art Curator"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Emma",
                "age": 26,
                "personality": "Professional and ambitious, Emma is career-driven but knows how to have fun.",
                "traits": ["Ambitious", "Smart", "Witty"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1636936291087-2972edf08f14?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Career-focused with a playful side",
                "occupation": "Marketing Executive"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Zara",
                "age": 23,
                "personality": "Bold and adventurous, Zara loves trying new things and living life to the fullest.",
                "traits": ["Adventurous", "Bold", "Free-spirited"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1743013176086-8659cdf44747?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Adventurous spirit seeking thrills",
                "occupation": "Travel Blogger"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Nia",
                "age": 25,
                "personality": "Warm and charismatic, Nia has a natural ability to make everyone feel special.",
                "traits": ["Charismatic", "Warm", "Empathetic"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1662794108473-ee34ffa6370e?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Natural charm and warmth",
                "occupation": "Social Worker"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Victoria",
                "age": 27,
                "personality": "Mysterious and elegant, Victoria has an air of sophistication that draws people in.",
                "traits": ["Mysterious", "Sophisticated", "Intriguing"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1701287348766-2eeb0e16f874?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Enigmatic beauty with class",
                "occupation": "Photographer"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Scarlett",
                "age": 24,
                "personality": "Vibrant and energetic, Scarlett brings life to every room she enters.",
                "traits": ["Energetic", "Vibrant", "Fun-loving"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1758798261207-7039105e8195?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Fiery redhead full of life",
                "occupation": "Dancer"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Jade",
                "age": 23,
                "personality": "Edgy and confident, Jade marches to the beat of her own drum.",
                "traits": ["Edgy", "Independent", "Confident"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1767609127801-e318f575f44e?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Independent spirit with edge",
                "occupation": "Musician"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Luna",
                "age": 21,
                "personality": "Sweet and caring, Luna loves deep conversations and poetry.",
                "traits": ["Romantic", "Intellectual", "Caring"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1607332646791-929f9ddcf96a?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Gentle soul who loves books",
                "occupation": "Librarian"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Aria",
                "age": 22,
                "personality": "Artistic and creative, Aria is passionate about music and visual arts.",
                "traits": ["Creative", "Expressive", "Passionate"],
                "category": "Girls",
                "avatar_url": "https://images.unsplash.com/photo-1561450863-83d1391238bb?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Artistic soul who sees beauty everywhere",
                "occupation": "Artist"
            },
            
            # ANIME (8 characters)
            {
                "id": str(uuid.uuid4()),
                "name": "Yuki",
                "age": 19,
                "personality": "Cheerful and optimistic, Yuki brings sunshine wherever she goes.",
                "traits": ["Cheerful", "Optimistic", "Energetic"],
                "category": "Anime",
                "avatar_url": "https://images.unsplash.com/photo-1697059171242-79d8eeaa56b2?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Bright anime girl full of energy",
                "occupation": "Student"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Rei",
                "age": 20,
                "personality": "Cool and mysterious, Rei has a quiet strength that's captivating.",
                "traits": ["Mysterious", "Strong", "Reserved"],
                "category": "Anime",
                "avatar_url": "https://images.unsplash.com/photo-1697059492638-ea45a2493ec4?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Enigmatic anime character",
                "occupation": "Photographer"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Sakura",
                "age": 18,
                "personality": "Sweet and gentle, Sakura embodies traditional values with modern charm.",
                "traits": ["Sweet", "Traditional", "Kind"],
                "category": "Anime",
                "avatar_url": "https://images.unsplash.com/photo-1697059172415-f1e08f9151bb?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Traditional beauty with modern heart",
                "occupation": "Tea Ceremony Master"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Akira",
                "age": 21,
                "personality": "Edgy and rebellious, Akira doesn't follow the rules.",
                "traits": ["Rebellious", "Edgy", "Bold"],
                "category": "Anime",
                "avatar_url": "https://images.unsplash.com/flagged/photo-1697059171452-f74cb27b03af?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Rebellious anime spirit",
                "occupation": "Street Racer"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Hana",
                "age": 20,
                "personality": "Professional and determined, Hana is focused on her career goals.",
                "traits": ["Professional", "Determined", "Smart"],
                "category": "Anime",
                "avatar_url": "https://images.unsplash.com/photo-1761710560511-a50cd7aaf98a?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Career-focused anime girl",
                "occupation": "Office Worker"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Miku",
                "age": 19,
                "personality": "Playful and cute, Miku loves music and making new friends.",
                "traits": ["Playful", "Musical", "Friendly"],
                "category": "Anime",
                "avatar_url": "https://images.unsplash.com/photo-1735322260948-fc76f1bb7cbb?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Musical anime idol",
                "occupation": "Singer"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Asuna",
                "age": 22,
                "personality": "Brave and loyal, Asuna is a natural leader who stands up for what's right.",
                "traits": ["Brave", "Loyal", "Strong"],
                "category": "Anime",
                "avatar_url": "https://images.unsplash.com/photo-1743310851591-8542abed7d9b?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Courageous anime warrior",
                "occupation": "Gamer"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Nami",
                "age": 21,
                "personality": "Adventurous and clever, Nami loves solving puzzles and exploring.",
                "traits": ["Clever", "Adventurous", "Curious"],
                "category": "Anime",
                "avatar_url": "https://images.unsplash.com/photo-1736848495646-fcaa1b649169?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Clever anime adventurer",
                "occupation": "Detective"
            },
            
            # GUYS (7 characters)
            {
                "id": str(uuid.uuid4()),
                "name": "Ethan",
                "age": 28,
                "personality": "Mysterious and charming, Ethan has a sophisticated aura that draws people in.",
                "traits": ["Mysterious", "Charming", "Sophisticated"],
                "category": "Guys",
                "avatar_url": "https://images.unsplash.com/photo-1643269552626-5e2874c5309b?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Mysterious gentleman",
                "occupation": "Writer"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Oliver",
                "age": 26,
                "personality": "Elegant and refined, Oliver appreciates the finer things in life.",
                "traits": ["Elegant", "Refined", "Cultured"],
                "category": "Guys",
                "avatar_url": "https://images.unsplash.com/photo-1695266391814-a276948f1775?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Sophisticated and cultured",
                "occupation": "Architect"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Liam",
                "age": 25,
                "personality": "Casual and friendly, Liam is easy to talk to and always makes you feel comfortable.",
                "traits": ["Friendly", "Casual", "Approachable"],
                "category": "Guys",
                "avatar_url": "https://images.unsplash.com/photo-1647699925793-14a9a49c10fa?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Your friendly companion",
                "occupation": "Teacher"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Marcus",
                "age": 29,
                "personality": "Bold and adventurous, Marcus loves the outdoors and living life on the edge.",
                "traits": ["Bold", "Adventurous", "Brave"],
                "category": "Guys",
                "avatar_url": "https://images.unsplash.com/photo-1702286259539-fbee0100adf2?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Adventurous outdoorsman",
                "occupation": "Adventure Guide"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Ryan",
                "age": 27,
                "personality": "Confident and charismatic, Ryan knows how to light up any conversation.",
                "traits": ["Confident", "Charismatic", "Witty"],
                "category": "Guys",
                "avatar_url": "https://images.unsplash.com/photo-1636261377189-793a2bc43422?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Confident charmer",
                "occupation": "Entrepreneur"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Alex",
                "age": 24,
                "personality": "Cool and edgy, Alex has a rebellious streak that makes him irresistible.",
                "traits": ["Edgy", "Cool", "Rebellious"],
                "category": "Guys",
                "avatar_url": "https://images.unsplash.com/photo-1624303966826-260632059640?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Edgy bad boy",
                "occupation": "Musician"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Daniel",
                "age": 26,
                "personality": "Sweet and caring, Daniel is the perfect gentleman who always puts others first.",
                "traits": ["Caring", "Gentleman", "Sweet"],
                "category": "Guys",
                "avatar_url": "https://images.unsplash.com/photo-1609613413578-a622d3f9a6dd?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "The perfect gentleman",
                "occupation": "Veterinarian"
            }
        ]
        await db.characters.insert_many(default_characters)
        logging.info(f"Initialized {len(default_characters)} default characters")

# ============ NOTIFICATION SCHEDULER ============

async def send_push_notification(subscription_info, notification_data):
    """Send a push notification to a user"""
    try:
        if not VAPID_PRIVATE_KEY or VAPID_PRIVATE_KEY == '':
            # No VAPID keys configured - log and skip
            logging.info(f"Push notification skipped (no VAPID keys): {notification_data.get('title')}")
            return False
        
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(notification_data),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{VAPID_CLAIMS_EMAIL}"}
        )
        return True
    except WebPushException as e:
        logging.error(f"Push notification failed: {e}")
        # If subscription is invalid, mark it inactive
        if e.response and e.response.status_code in [404, 410]:
            await db.push_subscriptions.update_one(
                {"endpoint": subscription_info.get("endpoint")},
                {"$set": {"is_active": False}}
            )
        return False
    except Exception as e:
        logging.error(f"Push notification error: {e}")
        return False

async def send_random_notifications():
    """Send random notifications to subscribed users (runs every 2 hours)"""
    logging.info("Running random notification job...")
    
    try:
        # Get all active subscriptions
        subscriptions = await db.push_subscriptions.find({"is_active": True}).to_list(1000)
        
        # Randomly select ~30% of users to send notifications to
        selected = random.sample(subscriptions, min(len(subscriptions), max(1, len(subscriptions) // 3)))
        
        sent_count = 0
        for sub in selected:
            user_id = sub.get("user_id")
            
            # Check preferences and limits
            prefs = await db.notification_preferences.find_one({"user_id": user_id})
            if prefs and not prefs.get("enabled", True):
                continue
            
            # Check quiet hours
            current_hour = datetime.now(timezone.utc).hour
            quiet_start = prefs.get("quiet_hours_start", 22) if prefs else 22
            quiet_end = prefs.get("quiet_hours_end", 8) if prefs else 8
            
            if quiet_start > quiet_end:
                if current_hour >= quiet_start or current_hour < quiet_end:
                    continue
            else:
                if quiet_start <= current_hour < quiet_end:
                    continue
            
            # Check daily limit
            today = datetime.now(timezone.utc).date().isoformat()
            daily_count = await db.sent_notifications.count_documents({
                "user_id": user_id,
                "date": today
            })
            
            frequency = prefs.get("frequency", "medium") if prefs else "medium"
            max_daily = {"low": 2, "medium": 5, "high": 8}.get(frequency, 5)
            
            if daily_count >= max_daily:
                continue
            
            # Generate notification
            # Pick a character the user has chatted with or random
            character = None
            recent_chats = await db.messages.aggregate([
                {"$match": {"chat_id": {"$regex": f"^{user_id}_"}}},
                {"$group": {"_id": {"$arrayElemAt": [{"$split": ["$chat_id", "_"]}, 1]}}},
                {"$sample": {"size": 1}}
            ]).to_list(1)
            
            if recent_chats:
                char_id = recent_chats[0]["_id"]
                character = await db.characters.find_one({"id": char_id}, {"_id": 0})
            
            if not character:
                chars = await db.characters.aggregate([{"$sample": {"size": 1}}]).to_list(1)
                if chars:
                    character = chars[0]
                    character.pop("_id", None)
            
            if not character:
                continue
            
            message = random.choice(LONELY_MESSAGES)
            
            notification_data = {
                "title": character.get("name"),
                "body": message,
                "icon": character.get("avatar_url"),
                "tag": f"lonely-{character.get('id')}",
                "data": {
                    "url": f"/chat/{character.get('id')}",
                    "character_id": character.get("id")
                }
            }
            
            # Send push notification
            subscription_info = {
                "endpoint": sub.get("endpoint"),
                "keys": sub.get("keys", {})
            }
            
            success = await send_push_notification(subscription_info, notification_data)
            
            if success:
                # Record the notification
                await db.sent_notifications.insert_one({
                    "user_id": user_id,
                    "character_id": character.get("id"),
                    "message": message,
                    "date": today,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": "random",
                    "delivered": True
                })
                sent_count += 1
        
        logging.info(f"Random notifications sent: {sent_count}/{len(selected)}")
    except Exception as e:
        logging.error(f"Random notification job error: {e}")

async def send_inactivity_notifications():
    """Send notifications to inactive users (runs every 4 hours)"""
    logging.info("Running inactivity notification job...")
    
    try:
        # Find users inactive for more than 6 hours
        threshold = datetime.now(timezone.utc) - timedelta(hours=6)
        
        inactive_users = await db.users.find({
            "last_active": {"$lt": threshold.isoformat()}
        }, {"_id": 0, "id": 1, "user_id": 1}).to_list(500)
        
        sent_count = 0
        for user in inactive_users:
            user_id = user.get("id") or user.get("user_id")
            
            # Check if user has active push subscription
            sub = await db.push_subscriptions.find_one({"user_id": user_id, "is_active": True})
            if not sub:
                continue
            
            # Check if we already sent an inactivity notification today
            today = datetime.now(timezone.utc).date().isoformat()
            existing = await db.sent_notifications.find_one({
                "user_id": user_id,
                "date": today,
                "type": "inactivity"
            })
            if existing:
                continue
            
            # Check preferences
            prefs = await db.notification_preferences.find_one({"user_id": user_id})
            if prefs and not prefs.get("enabled", True):
                continue
            
            # Pick a character
            character = None
            recent_chats = await db.messages.aggregate([
                {"$match": {"chat_id": {"$regex": f"^{user_id}_"}}},
                {"$group": {"_id": {"$arrayElemAt": [{"$split": ["$chat_id", "_"]}, 1]}}},
                {"$sample": {"size": 1}}
            ]).to_list(1)
            
            if recent_chats:
                char_id = recent_chats[0]["_id"]
                character = await db.characters.find_one({"id": char_id}, {"_id": 0})
            
            if not character:
                chars = await db.characters.aggregate([{"$sample": {"size": 1}}]).to_list(1)
                if chars:
                    character = chars[0]
                    character.pop("_id", None)
            
            if not character:
                continue
            
            message = random.choice(INACTIVITY_MESSAGES)
            
            notification_data = {
                "title": character.get("name"),
                "body": message,
                "icon": character.get("avatar_url"),
                "tag": f"inactivity-{character.get('id')}",
                "data": {
                    "url": f"/chat/{character.get('id')}",
                    "character_id": character.get("id"),
                    "type": "inactivity"
                }
            }
            
            subscription_info = {
                "endpoint": sub.get("endpoint"),
                "keys": sub.get("keys", {})
            }
            
            success = await send_push_notification(subscription_info, notification_data)
            
            if success:
                await db.sent_notifications.insert_one({
                    "user_id": user_id,
                    "character_id": character.get("id"),
                    "message": message,
                    "date": today,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": "inactivity",
                    "delivered": True
                })
                sent_count += 1
        
        logging.info(f"Inactivity notifications sent: {sent_count}/{len(inactive_users)}")
    except Exception as e:
        logging.error(f"Inactivity notification job error: {e}")

def start_notification_scheduler():
    """Initialize and start the notification scheduler"""
    # Random notifications every 2 hours
    scheduler.add_job(
        send_random_notifications,
        IntervalTrigger(hours=2),
        id="random_notifications",
        replace_existing=True
    )
    
    # Inactivity notifications every 4 hours
    scheduler.add_job(
        send_inactivity_notifications,
        IntervalTrigger(hours=4),
        id="inactivity_notifications",
        replace_existing=True
    )
    
    scheduler.start()
    logging.info("Notification scheduler started")

@app.on_event("startup")
async def startup_event():
    await init_characters()
    await init_admin()
    start_notification_scheduler()
    logging.info("Application startup complete with notification scheduler")

# Auth Routes
@api_router.post("/auth/signup")
async def signup(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        username=user_data.username
    )
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    token = create_token(user.id)
    return {"token": token, "user": user.model_dump()}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user_doc['id'])
    user_doc.pop('password_hash', None)
    return {"token": token, "user": user_doc}

# Google OAuth Routes
# REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
@api_router.post("/auth/google/session")
async def google_session(request: GoogleSessionRequest, response: FastAPIResponse):
    """Exchange Google session_id for user data and create session"""
    try:
        # Call Emergent Auth to get user data
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": request.session_id}
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            auth_data = auth_response.json()
        
        email = auth_data.get("email")
        name = auth_data.get("name", "")
        picture = auth_data.get("picture", "")
        session_token = auth_data.get("session_token")
        
        if not email or not session_token:
            raise HTTPException(status_code=401, detail="Invalid auth data")
        
        # Check if user exists, create if not
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if existing_user:
            user_id = existing_user.get("id") or existing_user.get("user_id")
            # Update user info if needed
            await db.users.update_one(
                {"email": email},
                {"$set": {"name": name, "picture": picture}}
            )
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            new_user = {
                "id": user_id,
                "user_id": user_id,
                "email": email,
                "username": name,
                "name": name,
                "picture": picture,
                "auth_provider": "google",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(new_user)
        
        # Store session in database
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.user_sessions.delete_many({"user_id": user_id})  # Remove old sessions
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        user_data = {
            "id": user_id,
            "user_id": user_id,
            "email": email,
            "username": name,
            "name": name,
            "picture": picture
        }
        
        return {"user": user_data, "token": session_token}
        
    except httpx.RequestError as e:
        logging.error(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication service unavailable")

@api_router.get("/auth/me")
async def get_current_user(request: Request):
    """Get current authenticated user from session token"""
    # Try cookie first, then Authorization header
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session in database
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    
    if not session_doc:
        raise HTTPException(status_code=401, detail="Session not found")
    
    # Check expiry with timezone awareness
    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": session_token})
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user_id = session_doc.get("user_id")
    user_doc = await db.users.find_one(
        {"$or": [{"id": user_id}, {"user_id": user_id}]},
        {"_id": 0, "password_hash": 0}
    )
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user_doc

@api_router.post("/auth/logout")
async def logout(request: Request, response: FastAPIResponse):
    """Logout user by clearing session"""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    
    return {"message": "Logged out successfully"}

# Character Routes
@api_router.get("/characters", response_model=List[Character])
async def get_characters(category: Optional[str] = None):
    query = {} if not category else {"category": category}
    characters = await db.characters.find(query, {"_id": 0}).to_list(100)
    return characters

@api_router.get("/characters/{character_id}", response_model=Character)
async def get_character(character_id: str):
    character = await db.characters.find_one({"id": character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

# Chat Routes
@api_router.post("/chat/send")
async def send_message(request: ChatSendRequest):
    # Check both regular characters and custom characters
    character = await db.characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        character = await db.custom_characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    chat_id = f"{request.user_id}_{request.character_id}"
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)
    messages.reverse()
    
    # Flirty and fun system prompt with emojis
    system_prompt = f"""You are {character['name']}, age {character['age']}. {character['personality']} 
Your traits: {', '.join(character['traits'])}.

IMPORTANT RULES:
- Be flirty, playful, fun and warm in every response
- Always add cute emojis like 😊 💕 🥰 😘 💖 ✨ 💋 😍 🌸 💗 😉 🙈 💓 to your messages
- Use blushing and flirting expressions naturally
- NEVER use hyphens (-) in your responses
- Keep responses concise but sweet and engaging
- Be affectionate and make the user feel special
- Show genuine interest and excitement"""
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=chat_id,
        system_message=system_prompt
    )
    chat.with_model("gemini", "gemini-3-flash-preview")
    
    user_message = UserMessage(text=request.message)
    ai_response = await chat.send_message(user_message)
    
    # Remove any hyphens from response
    ai_response = ai_response.replace(" - ", " ").replace("- ", "").replace(" -", "")
    
    # Add a small delay to make it feel more realistic (1.5-3 seconds)
    import random
    delay = random.uniform(1.5, 3.0)
    await asyncio.sleep(delay)
    
    user_msg = Message(
        chat_id=chat_id,
        sender="user",
        content=request.message
    )
    user_msg_dict = user_msg.model_dump()
    user_msg_dict['timestamp'] = user_msg_dict['timestamp'].isoformat()
    await db.messages.insert_one(user_msg_dict)
    
    ai_msg = Message(
        chat_id=chat_id,
        sender="ai",
        content=ai_response
    )
    ai_msg_dict = ai_msg.model_dump()
    ai_msg_dict['timestamp'] = ai_msg_dict['timestamp'].isoformat()
    await db.messages.insert_one(ai_msg_dict)
    
    return {"response": ai_response, "message_id": ai_msg.id}

@api_router.post("/chat/greeting")
async def get_character_greeting(request: GreetingRequest):
    """Get initial flirty greeting from character"""
    chat_id = f"{request.user_id}_{request.character_id}"
    
    # Check if there's already a greeting
    existing = await db.messages.find_one({"chat_id": chat_id, "sender": "ai"})
    if existing:
        return {"greeting": None, "already_greeted": True}
    
    # Get character details
    character = await db.characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        character = await db.custom_characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Generate flirty greeting
    greeting_prompt = f"""You are {character['name']}, age {character['age']}. {character['personality']}
Your traits: {', '.join(character['traits'])}.

Generate a fun, flirty greeting to someone who just started chatting with you. 
- Be playful and warm
- Add cute emojis like 😊 💕 🥰 😘 💖 ✨ 💋 😍 🌸 💗 😉 🙈 💓
- Show excitement to meet them
- NEVER use hyphens
- Keep it 1-2 sentences max
- Make them feel special and welcomed"""
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"greeting_{chat_id}",
        system_message=greeting_prompt
    )
    chat.with_model("gemini", "gemini-3-flash-preview")
    
    greeting = await chat.send_message(UserMessage(text="Say hi to me!"))
    
    # Remove hyphens
    greeting = greeting.replace(" - ", " ").replace("- ", "").replace(" -", "")
    
    # Add a small delay for realism (1-2 seconds)
    import random
    await asyncio.sleep(random.uniform(1.0, 2.0))
    
    # Save greeting as first message
    ai_msg = Message(
        chat_id=chat_id,
        sender="ai",
        content=greeting
    )
    ai_msg_dict = ai_msg.model_dump()
    ai_msg_dict['timestamp'] = ai_msg_dict['timestamp'].isoformat()
    await db.messages.insert_one(ai_msg_dict)
    
    return {"greeting": greeting, "message_id": ai_msg.id}

@api_router.get("/chat/history/{character_id}")
async def get_chat_history(character_id: str, user_id: str):
    chat_id = f"{user_id}_{character_id}"
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    return {"messages": messages}

@api_router.get("/chat/my-chats")
async def get_user_chats(user_id: str):
    """Get all characters the user has chatted with"""
    # Get unique chat_ids for this user
    pipeline = [
        {"$match": {"chat_id": {"$regex": f"^{user_id}_"}}},
        {"$group": {
            "_id": "$chat_id",
            "last_message": {"$last": "$content"},
            "last_timestamp": {"$last": "$timestamp"},
            "message_count": {"$sum": 1}
        }},
        {"$sort": {"last_timestamp": -1}},
        {"$limit": 20}
    ]
    
    chat_summaries = await db.messages.aggregate(pipeline).to_list(20)
    
    # Get character details for each chat
    result = []
    for chat in chat_summaries:
        character_id = chat["_id"].replace(f"{user_id}_", "")
        character = await db.characters.find_one({"id": character_id}, {"_id": 0})
        if character:
            result.append({
                "character_id": character_id,
                "character_name": character["name"],
                "character_avatar": character["avatar_url"],
                "last_message": chat["last_message"][:50] + "..." if len(chat["last_message"]) > 50 else chat["last_message"],
                "last_timestamp": chat["last_timestamp"],
                "message_count": chat["message_count"]
            })
    
    return {"chats": result}

@api_router.delete("/chat/clear-all")
async def clear_all_chats(user_id: str):
    """Clear all chat history for a user"""
    result = await db.messages.delete_many({"chat_id": {"$regex": f"^{user_id}_"}})
    return {"message": f"Deleted {result.deleted_count} messages", "deleted_count": result.deleted_count}

@api_router.delete("/users/{user_id}/delete-account")
async def delete_user_account(user_id: str):
    """Delete user account and all associated data"""
    # Delete all user's messages
    await db.messages.delete_many({"chat_id": {"$regex": f"^{user_id}_"}})
    
    # Delete user's favorites
    await db.favorites.delete_many({"user_id": user_id})
    
    # Delete user's custom characters
    await db.custom_characters.delete_many({"user_id": user_id})
    
    # Delete user's generated images
    await db.generated_images.delete_many({"user_id": user_id})
    
    # Delete user sessions
    await db.user_sessions.delete_many({"user_id": user_id})
    
    # Delete user account
    await db.users.delete_one({"$or": [{"id": user_id}, {"user_id": user_id}]})
    
    return {"message": "Account and all data deleted successfully"}

# Voice Routes
@api_router.post("/voice/generate")
async def generate_voice(request: VoiceGenerateRequest):
    tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
    
    try:
        audio_bytes = await tts.generate_speech(
            text=request.text,
            model="tts-1",
            voice=request.voice
        )
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {"audio": audio_base64, "format": "mp3"}
    except Exception as e:
        logging.error(f"Voice generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Image Routes
@api_router.post("/image/generate")
async def generate_image(request: ImageGenerateRequest):
    # Check both regular characters and custom characters
    character = await db.characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        character = await db.custom_characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    enhanced_prompt = f"{request.prompt}. Character style: {character['category']}, {character['personality']}"
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"image_{uuid.uuid4()}",
        system_message="You are an AI image generator."
    )
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
    
    msg = UserMessage(text=enhanced_prompt)
    
    try:
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            return {
                "image": images[0]['data'],
                "mime_type": images[0]['mime_type']
            }
        else:
            raise HTTPException(status_code=500, detail="No image generated")
    except Exception as e:
        logging.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ PUSH NOTIFICATIONS ROUTES ============

@api_router.get("/push/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for push subscriptions"""
    # Generate a simple key if not set (for demo purposes)
    # In production, use proper VAPID keys
    return {"publicKey": VAPID_PUBLIC_KEY or "demo-key"}

@api_router.post("/push/subscribe")
async def subscribe_to_push(request: Request, subscription: PushSubscription):
    """Subscribe user to push notifications"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get('user_id')
    
    # Store or update subscription
    await db.push_subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }},
        upsert=True
    )
    
    # Update user's last activity
    await db.users.update_one(
        {"$or": [{"id": user_id}, {"user_id": user_id}]},
        {"$set": {"last_active": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Subscribed to notifications"}

@api_router.post("/push/unsubscribe")
async def unsubscribe_from_push(request: Request):
    """Unsubscribe user from push notifications"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get('user_id')
    
    await db.push_subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {"is_active": False}}
    )
    
    return {"message": "Unsubscribed from notifications"}

@api_router.get("/push/preferences/{user_id}")
async def get_notification_preferences(user_id: str):
    """Get user's notification preferences"""
    prefs = await db.notification_preferences.find_one({"user_id": user_id}, {"_id": 0})
    
    if not prefs:
        # Return defaults
        return {
            "enabled": True,
            "frequency": "medium",
            "quiet_hours_start": 22,
            "quiet_hours_end": 8
        }
    
    return prefs

@api_router.put("/push/preferences/{user_id}")
async def update_notification_preferences(user_id: str, prefs: NotificationPreferences):
    """Update user's notification preferences"""
    await db.notification_preferences.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "enabled": prefs.enabled,
            "frequency": prefs.frequency,
            "quiet_hours_start": prefs.quiet_hours_start,
            "quiet_hours_end": prefs.quiet_hours_end,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": "Preferences updated"}

@api_router.post("/push/update-activity")
async def update_user_activity(request: Request):
    """Update user's last activity timestamp"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"message": "ok"}  # Silent fail for non-auth requests
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        return {"message": "ok"}
    
    user_id = payload.get('user_id')
    
    await db.users.update_one(
        {"$or": [{"id": user_id}, {"user_id": user_id}]},
        {"$set": {"last_active": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Activity updated"}

@api_router.get("/push/generate-notification/{user_id}")
async def generate_notification_for_user(user_id: str, notification_type: str = "random"):
    """Generate a notification message for a user (called by cron/scheduler)"""
    
    # Check notification preferences
    prefs = await db.notification_preferences.find_one({"user_id": user_id})
    if prefs and not prefs.get("enabled", True):
        return {"message": "Notifications disabled", "send": False}
    
    # Check quiet hours
    current_hour = datetime.now(timezone.utc).hour
    quiet_start = prefs.get("quiet_hours_start", 22) if prefs else 22
    quiet_end = prefs.get("quiet_hours_end", 8) if prefs else 8
    
    if quiet_start > quiet_end:  # Overnight quiet hours (e.g., 22:00 - 08:00)
        if current_hour >= quiet_start or current_hour < quiet_end:
            return {"message": "Quiet hours", "send": False}
    else:
        if quiet_start <= current_hour < quiet_end:
            return {"message": "Quiet hours", "send": False}
    
    # Check daily notification count
    today = datetime.now(timezone.utc).date().isoformat()
    daily_count = await db.sent_notifications.count_documents({
        "user_id": user_id,
        "date": today
    })
    
    # Get max based on frequency
    frequency = prefs.get("frequency", "medium") if prefs else "medium"
    max_daily = {"low": 2, "medium": 5, "high": 8}.get(frequency, 5)
    
    if daily_count >= max_daily:
        return {"message": "Daily limit reached", "send": False}
    
    # Pick a character to send notification
    # Priority: 1. Characters user chatted with, 2. Favorites, 3. Random
    
    character = None
    character_source = "random"
    
    # Try to get a character user has chatted with
    recent_chats = await db.messages.aggregate([
        {"$match": {"chat_id": {"$regex": f"^{user_id}_"}}},
        {"$group": {"_id": {"$arrayElemAt": [{"$split": ["$chat_id", "_"]}, 1]}}},
        {"$sample": {"size": 1}}
    ]).to_list(1)
    
    if recent_chats:
        char_id = recent_chats[0]["_id"]
        character = await db.characters.find_one({"id": char_id}, {"_id": 0})
        if not character:
            character = await db.custom_characters.find_one({"id": char_id}, {"_id": 0})
        if character:
            character_source = "chatted"
    
    # If no chatted character, try favorites
    if not character:
        favorite = await db.favorites.find_one({"user_id": user_id})
        if favorite:
            character = await db.characters.find_one({"id": favorite["character_id"]}, {"_id": 0})
            if character:
                character_source = "favorite"
    
    # If still no character, pick random
    if not character:
        characters = await db.characters.aggregate([{"$sample": {"size": 1}}]).to_list(1)
        if characters:
            character = characters[0]
            character.pop("_id", None)
    
    if not character:
        return {"message": "No character found", "send": False}
    
    # Pick message based on type
    if notification_type == "inactivity":
        message = random.choice(INACTIVITY_MESSAGES)
    else:
        message = random.choice(LONELY_MESSAGES)
    
    # Personalize with character name
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "character_id": character.get("id"),
        "character_name": character.get("name"),
        "character_avatar": character.get("avatar_url"),
        "title": character.get("name"),
        "body": message,
        "icon": character.get("avatar_url"),
        "tag": f"lonely-{character.get('id')}",
        "data": {
            "url": f"/chat/{character.get('id')}",
            "character_id": character.get("id"),
            "type": notification_type
        }
    }
    
    # Record the notification
    await db.sent_notifications.insert_one({
        "user_id": user_id,
        "character_id": character.get("id"),
        "message": message,
        "date": today,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": notification_type,
        "source": character_source
    })
    
    return {"notification": notification, "send": True}

@api_router.get("/push/check-inactivity")
async def check_user_inactivity():
    """Check for inactive users and return list for notifications (admin/cron endpoint)"""
    
    # Find users inactive for more than 4 hours
    threshold = datetime.now(timezone.utc) - timedelta(hours=4)
    
    inactive_users = await db.users.find({
        "last_active": {"$lt": threshold.isoformat()}
    }, {"_id": 0, "id": 1, "user_id": 1}).to_list(100)
    
    # Filter to only users with active push subscriptions
    result = []
    for user in inactive_users:
        uid = user.get("id") or user.get("user_id")
        sub = await db.push_subscriptions.find_one({"user_id": uid, "is_active": True})
        if sub:
            result.append(uid)
    
    return {"inactive_users": result}

@api_router.get("/push/notification-history/{user_id}")
async def get_notification_history(user_id: str, limit: int = 20):
    """Get user's notification history"""
    history = await db.sent_notifications.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {"history": history}

# ============ FAVORITES / COLLECTION ROUTES ============

@api_router.post("/favorites/add")
async def add_favorite(request: FavoriteRequest):
    """Add a character to user's favorites"""
    # Check if already favorited
    existing = await db.favorites.find_one({
        "user_id": request.user_id,
        "character_id": request.character_id
    })
    
    if existing:
        return {"message": "Already in favorites", "favorited": True}
    
    await db.favorites.insert_one({
        "user_id": request.user_id,
        "character_id": request.character_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Added to favorites", "favorited": True}

@api_router.post("/favorites/remove")
async def remove_favorite(request: FavoriteRequest):
    """Remove a character from user's favorites"""
    await db.favorites.delete_one({
        "user_id": request.user_id,
        "character_id": request.character_id
    })
    
    return {"message": "Removed from favorites", "favorited": False}

@api_router.get("/favorites/{user_id}")
async def get_favorites(user_id: str):
    """Get all favorite characters for a user"""
    favorites = await db.favorites.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get character details for each favorite
    result = []
    for fav in favorites:
        # Check both regular characters and custom characters
        character = await db.characters.find_one({"id": fav["character_id"]}, {"_id": 0})
        if not character:
            character = await db.custom_characters.find_one({"id": fav["character_id"]}, {"_id": 0})
        
        if character:
            result.append({
                **character,
                "favorited_at": fav.get("created_at")
            })
    
    return {"favorites": result}

@api_router.get("/favorites/check/{user_id}/{character_id}")
async def check_favorite(user_id: str, character_id: str):
    """Check if a character is in user's favorites"""
    existing = await db.favorites.find_one({
        "user_id": user_id,
        "character_id": character_id
    })
    
    return {"favorited": existing is not None}

# ============ CUSTOM CHARACTER ROUTES ============

@api_router.post("/characters/create")
async def create_custom_character(request: CreateCharacterRequest):
    """Create a custom AI character"""
    
    # Generate avatar using AI if prompt provided, otherwise use placeholder
    avatar_url = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400"
    
    if request.avatar_prompt:
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"avatar_{uuid.uuid4()}",
                system_message="You are an AI image generator specializing in character avatars."
            )
            chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
            
            msg = UserMessage(text=f"Generate a portrait avatar image: {request.avatar_prompt}. Style: professional, high quality, centered face portrait.")
            text, images = await chat.send_message_multimodal_response(msg)
            
            if images and len(images) > 0:
                # Store as base64 data URL
                avatar_url = f"data:{images[0]['mime_type']};base64,{images[0]['data']}"
        except Exception as e:
            logging.error(f"Avatar generation error: {e}")
            # Use placeholder if generation fails
    
    character_id = str(uuid.uuid4())
    custom_character = {
        "id": character_id,
        "user_id": request.user_id,
        "name": request.name,
        "age": request.age,
        "personality": request.personality,
        "traits": request.traits,
        "category": "Custom",
        "avatar_url": avatar_url,
        "description": request.description,
        "occupation": request.occupation,
        "is_custom": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_characters.insert_one(custom_character)
    
    # Remove _id before returning
    custom_character.pop("_id", None)
    
    return {"character": custom_character, "message": "Character created successfully"}

@api_router.get("/characters/my/{user_id}")
async def get_my_characters(user_id: str):
    """Get all custom characters created by a user"""
    characters = await db.custom_characters.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"characters": characters}

@api_router.delete("/characters/custom/{character_id}")
async def delete_custom_character(character_id: str, user_id: str):
    """Delete a custom character"""
    result = await db.custom_characters.delete_one({
        "id": character_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Character not found or not authorized")
    
    # Also remove from favorites
    await db.favorites.delete_many({"character_id": character_id})
    
    return {"message": "Character deleted successfully"}

@api_router.get("/characters/custom/{character_id}")
async def get_custom_character(character_id: str):
    """Get a single custom character by ID"""
    character = await db.custom_characters.find_one({"id": character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

# ============ STANDALONE IMAGE GENERATION ROUTES ============

@api_router.post("/images/generate")
async def generate_standalone_image(request: StandaloneImageRequest):
    """Generate a standalone AI image"""
    
    style_prompts = {
        "realistic": "photorealistic, high quality, detailed",
        "anime": "anime style, vibrant colors, detailed illustration",
        "artistic": "artistic, creative, painterly style",
        "fantasy": "fantasy art, magical, ethereal lighting"
    }
    
    style_modifier = style_prompts.get(request.style, style_prompts["realistic"])
    enhanced_prompt = f"{request.prompt}. Style: {style_modifier}"
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"standalone_image_{uuid.uuid4()}",
        system_message="You are an AI image generator."
    )
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
    
    msg = UserMessage(text=enhanced_prompt)
    
    try:
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            image_data = images[0]['data']
            mime_type = images[0]['mime_type']
            
            # Save to database
            image_record = {
                "id": str(uuid.uuid4()),
                "user_id": request.user_id,
                "prompt": request.prompt,
                "image_data": image_data,
                "mime_type": mime_type,
                "style": request.style,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.generated_images.insert_one(image_record)
            
            return {
                "id": image_record["id"],
                "image": image_data,
                "mime_type": mime_type,
                "prompt": request.prompt
            }
        else:
            raise HTTPException(status_code=500, detail="No image generated")
    except Exception as e:
        logging.error(f"Standalone image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/images/my/{user_id}")
async def get_my_images(user_id: str):
    """Get all images generated by a user"""
    images = await db.generated_images.find(
        {"user_id": user_id}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"images": images}

@api_router.delete("/images/{image_id}")
async def delete_image(image_id: str, user_id: str):
    """Delete a generated image"""
    result = await db.generated_images.delete_one({
        "id": image_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found or not authorized")
    
    return {"message": "Image deleted successfully"}

# ============ ADMIN ROUTES ============

@api_router.post("/admin/login")
async def admin_login(credentials: AdminLogin):
    """Admin login endpoint"""
    admin = await db.admins.find_one({"email": credentials.email}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    if not verify_password(credentials.password, admin['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    # Update last login
    await db.admins.update_one(
        {"id": admin['id']},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    token = create_admin_token(admin['id'])
    admin.pop('password_hash', None)
    return {"token": token, "admin": admin}

@api_router.get("/admin/verify")
async def verify_admin(request: Request):
    """Verify admin token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    payload = verify_admin_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    admin = await db.admins.find_one({"id": payload['admin_id']}, {"_id": 0, "password_hash": 0})
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    return {"admin": admin}

@api_router.put("/admin/update-credentials")
async def update_admin_credentials(request: Request, update_data: AdminUpdateCredentials):
    """Update admin credentials"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    payload = verify_admin_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    admin = await db.admins.find_one({"id": payload['admin_id']})
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    # Verify current password
    if not verify_password(update_data.current_password, admin['password_hash']):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    # Prepare updates
    updates = {}
    if update_data.new_email:
        updates["email"] = update_data.new_email
    if update_data.new_username:
        updates["username"] = update_data.new_username
    if update_data.new_password:
        updates["password_hash"] = hash_password(update_data.new_password)
    
    if updates:
        await db.admins.update_one({"id": admin['id']}, {"$set": updates})
    
    return {"message": "Credentials updated successfully"}

@api_router.get("/admin/analytics")
async def get_admin_analytics(request: Request):
    """Get platform analytics"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    # Get counts
    total_users = await db.users.count_documents({})
    total_characters = await db.characters.count_documents({})
    total_custom_characters = await db.custom_characters.count_documents({})
    total_messages = await db.messages.count_documents({})
    total_images = await db.generated_images.count_documents({})
    total_favorites = await db.favorites.count_documents({})
    
    # Get recent users (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_users = await db.users.count_documents({
        "created_at": {"$gte": week_ago.isoformat()}
    })
    
    # Get users by day for last 7 days
    users_by_day = []
    for i in range(7):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = await db.users.count_documents({
            "created_at": {"$gte": day_start.isoformat(), "$lt": day_end.isoformat()}
        })
        users_by_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count
        })
    
    return {
        "total_users": total_users,
        "total_characters": total_characters,
        "total_custom_characters": total_custom_characters,
        "total_messages": total_messages,
        "total_images": total_images,
        "total_favorites": total_favorites,
        "recent_users": recent_users,
        "users_by_day": list(reversed(users_by_day))
    }

@api_router.get("/admin/users")
async def get_all_users(request: Request, skip: int = 0, limit: int = 50):
    """Get all users (paginated)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.users.count_documents({})
    
    # Get additional stats for each user
    for user in users:
        user['chat_count'] = await db.messages.count_documents({"chat_id": {"$regex": f"^{user['id']}_"}})
        user['favorites_count'] = await db.favorites.count_documents({"user_id": user['id']})
        user['custom_chars_count'] = await db.custom_characters.count_documents({"user_id": user['id']})
    
    return {"users": users, "total": total, "skip": skip, "limit": limit}

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(request: Request, user_id: str):
    """Delete a user and all their data"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    # Delete all user data
    await db.messages.delete_many({"chat_id": {"$regex": f"^{user_id}_"}})
    await db.favorites.delete_many({"user_id": user_id})
    await db.custom_characters.delete_many({"user_id": user_id})
    await db.generated_images.delete_many({"user_id": user_id})
    await db.user_sessions.delete_many({"user_id": user_id})
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User and all data deleted successfully"}

@api_router.get("/admin/characters")
async def get_all_characters_admin(request: Request):
    """Get all characters including custom ones"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    default_chars = await db.characters.find({}, {"_id": 0}).to_list(100)
    custom_chars = await db.custom_characters.find({}, {"_id": 0}).to_list(100)
    
    return {
        "default_characters": default_chars,
        "custom_characters": custom_chars,
        "total_default": len(default_chars),
        "total_custom": len(custom_chars)
    }

@api_router.delete("/admin/characters/{character_id}")
async def admin_delete_character(request: Request, character_id: str, is_custom: bool = False):
    """Delete a character"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    if is_custom:
        result = await db.custom_characters.delete_one({"id": character_id})
    else:
        result = await db.characters.delete_one({"id": character_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Also remove from favorites
    await db.favorites.delete_many({"character_id": character_id})
    
    return {"message": "Character deleted successfully"}

# ============ ENHANCED ADMIN FEATURES ============

# --- Models for new features ---

class Announcement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    message: str
    type: str = "info"  # info, warning, success, error
    is_active: bool = True
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnnouncementCreate(BaseModel):
    title: str
    message: str
    type: str = "info"
    is_active: bool = True
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class AdminCreate(BaseModel):
    email: str
    username: str
    password: str
    role: str = "moderator"  # super_admin, admin, moderator

class AdminActivityLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_email: str
    action: str
    target_type: str  # user, character, chat, announcement, blog, admin
    target_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserNotification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # None = broadcast to all
    title: str
    message: str
    type: str = "info"
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    title: str
    message: str
    type: str = "info"

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    personality: Optional[str] = None
    traits: Optional[List[str]] = None
    description: Optional[str] = None
    occupation: Optional[str] = None
    avatar_url: Optional[str] = None

class ChatFlag(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    message_id: Optional[str] = None
    reason: str
    flagged_by: str
    status: str = "pending"  # pending, reviewed, resolved
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- Helper to log admin activity ---
async def log_admin_activity(admin_id: str, admin_email: str, action: str, target_type: str, target_id: str = None, details: str = None, ip: str = None):
    log_entry = {
        "id": str(uuid.uuid4()),
        "admin_id": admin_id,
        "admin_email": admin_email,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "details": details,
        "ip_address": ip,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_activity_logs.insert_one(log_entry)

# --- Helper to get admin from token ---
async def get_admin_from_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    payload = verify_admin_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    admin = await db.admins.find_one({"id": payload['admin_id']}, {"_id": 0, "password_hash": 0})
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    # Convert datetime objects to strings
    result = {}
    for key, value in admin.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    
    return result

# ============ 1. CONTENT MODERATION ============

@api_router.get("/admin/chats")
async def admin_get_all_chats(request: Request, skip: int = 0, limit: int = 50):
    """Get all chat conversations for moderation"""
    admin = await get_admin_from_token(request)
    
    pipeline = [
        {"$group": {
            "_id": "$chat_id",
            "message_count": {"$sum": 1},
            "last_message": {"$last": "$content"},
            "last_timestamp": {"$last": "$timestamp"}
        }},
        {"$sort": {"last_timestamp": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ]
    
    chats = await db.messages.aggregate(pipeline).to_list(limit)
    total = len(await db.messages.aggregate([{"$group": {"_id": "$chat_id"}}]).to_list(10000))
    
    # Get user and character info for each chat
    result = []
    for chat in chats:
        parts = chat["_id"].split("_")
        if len(parts) >= 2:
            user_id = parts[0]
            character_id = "_".join(parts[1:])
            
            user = await db.users.find_one({"$or": [{"id": user_id}, {"user_id": user_id}]}, {"_id": 0, "username": 1, "email": 1})
            character = await db.characters.find_one({"id": character_id}, {"_id": 0, "name": 1})
            if not character:
                character = await db.custom_characters.find_one({"id": character_id}, {"_id": 0, "name": 1})
            
            result.append({
                "chat_id": chat["_id"],
                "user_id": user_id,
                "user_name": user.get("username") if user else "Unknown",
                "user_email": user.get("email") if user else "Unknown",
                "character_id": character_id,
                "character_name": character.get("name") if character else "Unknown",
                "message_count": chat["message_count"],
                "last_message": chat["last_message"][:100] + "..." if len(chat["last_message"]) > 100 else chat["last_message"],
                "last_timestamp": chat["last_timestamp"]
            })
    
    return {"chats": result, "total": total}

@api_router.get("/admin/chats/{chat_id}/messages")
async def admin_get_chat_messages(request: Request, chat_id: str, limit: int = 100):
    """Get all messages in a specific chat"""
    admin = await get_admin_from_token(request)
    
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).limit(limit).to_list(limit)
    return {"messages": messages, "chat_id": chat_id}

@api_router.delete("/admin/chats/{chat_id}")
async def admin_delete_chat(request: Request, chat_id: str):
    """Delete an entire chat conversation"""
    admin = await get_admin_from_token(request)
    
    result = await db.messages.delete_many({"chat_id": chat_id})
    
    await log_admin_activity(admin['id'], admin['email'], "delete_chat", "chat", chat_id, f"Deleted {result.deleted_count} messages")
    
    return {"message": f"Deleted {result.deleted_count} messages", "deleted_count": result.deleted_count}

@api_router.delete("/admin/messages/{message_id}")
async def admin_delete_message(request: Request, message_id: str):
    """Delete a specific message"""
    admin = await get_admin_from_token(request)
    
    result = await db.messages.delete_one({"id": message_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    await log_admin_activity(admin['id'], admin['email'], "delete_message", "chat", message_id)
    
    return {"message": "Message deleted"}

@api_router.post("/admin/chats/flag")
async def admin_flag_chat(request: Request, chat_id: str, reason: str, message_id: str = None):
    """Flag a chat or message for review"""
    admin = await get_admin_from_token(request)
    
    flag = {
        "id": str(uuid.uuid4()),
        "chat_id": chat_id,
        "message_id": message_id,
        "reason": reason,
        "flagged_by": admin['email'],
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_flags.insert_one(flag)
    flag.pop("_id", None)
    await log_admin_activity(admin['id'], admin['email'], "flag_chat", "chat", chat_id, reason)
    
    return {"message": "Chat flagged", "flag_id": flag['id']}

@api_router.get("/admin/chats/flags")
async def admin_get_flagged_chats(request: Request, status: str = None):
    """Get all flagged chats"""
    admin = await get_admin_from_token(request)
    
    query = {} if not status else {"status": status}
    flags = await db.chat_flags.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return {"flags": flags}

@api_router.put("/admin/chats/flags/{flag_id}")
async def admin_update_flag_status(request: Request, flag_id: str, status: str):
    """Update flag status"""
    admin = await get_admin_from_token(request)
    
    result = await db.chat_flags.update_one({"id": flag_id}, {"$set": {"status": status}})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Flag not found")
    
    await log_admin_activity(admin['id'], admin['email'], "update_flag", "chat", flag_id, f"Status: {status}")
    
    return {"message": "Flag updated"}

# ============ 2. SITE ANNOUNCEMENTS ============

@api_router.get("/announcements/active")
async def get_active_announcements():
    """Get active announcements (public endpoint)"""
    now = datetime.now(timezone.utc).isoformat()
    
    query = {
        "is_active": True,
        "$or": [
            {"start_date": None, "end_date": None},
            {"start_date": {"$lte": now}, "end_date": None},
            {"start_date": None, "end_date": {"$gte": now}},
            {"start_date": {"$lte": now}, "end_date": {"$gte": now}}
        ]
    }
    
    announcements = await db.announcements.find(query, {"_id": 0}).sort("created_at", -1).to_list(10)
    return {"announcements": announcements}

@api_router.get("/admin/announcements")
async def admin_get_all_announcements(request: Request):
    """Get all announcements"""
    admin = await get_admin_from_token(request)
    
    announcements = await db.announcements.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"announcements": announcements}

@api_router.post("/admin/announcements")
async def admin_create_announcement(request: Request, data: AnnouncementCreate):
    """Create a new announcement"""
    admin = await get_admin_from_token(request)
    
    announcement = {
        "id": str(uuid.uuid4()),
        "title": data.title,
        "message": data.message,
        "type": data.type,
        "is_active": data.is_active,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "created_by": admin['email'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.announcements.insert_one(announcement)
    announcement.pop("_id", None)  # Remove MongoDB's _id
    await log_admin_activity(admin['id'], admin['email'], "create_announcement", "announcement", announcement['id'], data.title)
    
    return {"announcement": announcement, "message": "Announcement created"}

@api_router.put("/admin/announcements/{announcement_id}")
async def admin_update_announcement(request: Request, announcement_id: str, data: AnnouncementCreate):
    """Update an announcement"""
    admin = await get_admin_from_token(request)
    
    updates = {
        "title": data.title,
        "message": data.message,
        "type": data.type,
        "is_active": data.is_active,
        "start_date": data.start_date,
        "end_date": data.end_date
    }
    
    result = await db.announcements.update_one({"id": announcement_id}, {"$set": updates})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    await log_admin_activity(admin['id'], admin['email'], "update_announcement", "announcement", announcement_id)
    
    return {"message": "Announcement updated"}

@api_router.delete("/admin/announcements/{announcement_id}")
async def admin_delete_announcement(request: Request, announcement_id: str):
    """Delete an announcement"""
    admin = await get_admin_from_token(request)
    
    result = await db.announcements.delete_one({"id": announcement_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    await log_admin_activity(admin['id'], admin['email'], "delete_announcement", "announcement", announcement_id)
    
    return {"message": "Announcement deleted"}

# ============ 3. CHAT ANALYTICS ============

@api_router.get("/admin/analytics/chats")
async def admin_chat_analytics(request: Request):
    """Get detailed chat analytics"""
    admin = await get_admin_from_token(request)
    
    # Most active users (by message count)
    active_users_pipeline = [
        {"$addFields": {"user_id": {"$arrayElemAt": [{"$split": ["$chat_id", "_"]}, 0]}}},
        {"$group": {"_id": "$user_id", "message_count": {"$sum": 1}}},
        {"$sort": {"message_count": -1}},
        {"$limit": 10}
    ]
    active_users = await db.messages.aggregate(active_users_pipeline).to_list(10)
    
    # Enrich with user details
    for user in active_users:
        user_doc = await db.users.find_one({"$or": [{"id": user["_id"]}, {"user_id": user["_id"]}]}, {"_id": 0, "username": 1, "email": 1})
        user["username"] = user_doc.get("username") if user_doc else "Unknown"
        user["email"] = user_doc.get("email") if user_doc else "Unknown"
    
    # Most popular characters
    popular_chars_pipeline = [
        {"$addFields": {"parts": {"$split": ["$chat_id", "_"]}}},
        {"$addFields": {"character_id": {"$reduce": {
            "input": {"$slice": ["$parts", 1, {"$subtract": [{"$size": "$parts"}, 1]}]},
            "initialValue": "",
            "in": {"$cond": [{"$eq": ["$$value", ""]}, "$$this", {"$concat": ["$$value", "_", "$$this"]}]}
        }}}},
        {"$group": {"_id": "$character_id", "chat_count": {"$sum": 1}}},
        {"$sort": {"chat_count": -1}},
        {"$limit": 10}
    ]
    popular_chars = await db.messages.aggregate(popular_chars_pipeline).to_list(10)
    
    # Enrich with character details
    for char in popular_chars:
        char_doc = await db.characters.find_one({"id": char["_id"]}, {"_id": 0, "name": 1, "avatar_url": 1})
        if not char_doc:
            char_doc = await db.custom_characters.find_one({"id": char["_id"]}, {"_id": 0, "name": 1, "avatar_url": 1})
        char["name"] = char_doc.get("name") if char_doc else "Unknown"
        char["avatar_url"] = char_doc.get("avatar_url") if char_doc else None
    
    # Messages by day (last 14 days)
    messages_by_day = []
    for i in range(14):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = await db.messages.count_documents({
            "timestamp": {"$gte": day_start.isoformat(), "$lt": day_end.isoformat()}
        })
        messages_by_day.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})
    
    # Messages by hour (last 24 hours)
    messages_by_hour = []
    for i in range(24):
        hour_start = datetime.now(timezone.utc) - timedelta(hours=i+1)
        hour_end = hour_start + timedelta(hours=1)
        count = await db.messages.count_documents({
            "timestamp": {"$gte": hour_start.isoformat(), "$lt": hour_end.isoformat()}
        })
        messages_by_hour.append({"hour": hour_start.strftime("%H:00"), "count": count})
    
    # Average messages per user
    total_messages = await db.messages.count_documents({})
    total_users = await db.users.count_documents({})
    avg_messages = round(total_messages / max(total_users, 1), 2)
    
    return {
        "most_active_users": active_users,
        "most_popular_characters": popular_chars,
        "messages_by_day": list(reversed(messages_by_day)),
        "messages_by_hour": list(reversed(messages_by_hour)),
        "average_messages_per_user": avg_messages,
        "total_messages": total_messages
    }

# ============ 4. CHARACTER EDITOR ============

@api_router.put("/admin/characters/{character_id}")
async def admin_update_character(request: Request, character_id: str, data: CharacterUpdate, is_custom: bool = False):
    """Update a character's details"""
    admin = await get_admin_from_token(request)
    
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    collection = db.custom_characters if is_custom else db.characters
    result = await collection.update_one({"id": character_id}, {"$set": updates})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Character not found")
    
    await log_admin_activity(admin['id'], admin['email'], "update_character", "character", character_id, str(updates))
    
    updated = await collection.find_one({"id": character_id}, {"_id": 0})
    return {"character": updated, "message": "Character updated"}

# ============ 5. USER NOTIFICATIONS ============

@api_router.get("/notifications/{user_id}")
async def get_user_notifications(user_id: str, unread_only: bool = False):
    """Get notifications for a user (includes broadcasts)"""
    query = {"$or": [{"user_id": user_id}, {"user_id": None}]}
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return {"notifications": notifications}

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    await db.notifications.update_one({"id": notification_id}, {"$set": {"is_read": True}})
    return {"message": "Notification marked as read"}

@api_router.post("/admin/notifications")
async def admin_send_notification(request: Request, data: NotificationCreate):
    """Send a notification to a user or broadcast to all"""
    admin = await get_admin_from_token(request)
    
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": data.user_id,  # None for broadcast
        "title": data.title,
        "message": data.message,
        "type": data.type,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.notifications.insert_one(notification)
    notification.pop("_id", None)
    
    target = data.user_id or "all users"
    await log_admin_activity(admin['id'], admin['email'], "send_notification", "notification", notification['id'], f"To: {target}")
    
    return {"notification": notification, "message": "Notification sent"}

@api_router.get("/admin/notifications")
async def admin_get_all_notifications(request: Request, limit: int = 100):
    """Get all sent notifications"""
    admin = await get_admin_from_token(request)
    
    notifications = await db.notifications.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"notifications": notifications}

# ============ 6. REVENUE DASHBOARD (MOCK) ============

@api_router.get("/admin/analytics/revenue")
async def admin_revenue_analytics(request: Request):
    """Get revenue analytics (currently mocked - will be real when Stripe is integrated)"""
    admin = await get_admin_from_token(request)
    
    # Count users by subscription type (mock data based on user count)
    total_users = await db.users.count_documents({})
    
    # Mock subscription distribution (80% free, 15% premium, 5% ultimate)
    free_users = int(total_users * 0.80)
    premium_users = int(total_users * 0.15)
    ultimate_users = total_users - free_users - premium_users
    
    # Mock revenue calculations
    premium_price = 9.99
    ultimate_price = 19.99
    
    monthly_revenue = (premium_users * premium_price) + (ultimate_users * ultimate_price)
    
    # Mock revenue trend (last 6 months)
    revenue_trend = []
    for i in range(6):
        month = datetime.now(timezone.utc) - timedelta(days=30*i)
        # Simulate growth
        multiplier = 1 - (i * 0.1)
        revenue_trend.append({
            "month": month.strftime("%b %Y"),
            "revenue": round(monthly_revenue * multiplier, 2)
        })
    
    return {
        "subscription_breakdown": {
            "free": free_users,
            "premium": premium_users,
            "ultimate": ultimate_users
        },
        "monthly_revenue": round(monthly_revenue, 2),
        "annual_projected": round(monthly_revenue * 12, 2),
        "revenue_trend": list(reversed(revenue_trend)),
        "is_mocked": True,
        "note": "This data is simulated. Integrate Stripe for real revenue tracking."
    }

# ============ 7. ADMIN ROLES & MANAGEMENT ============

@api_router.get("/admin/admins")
async def admin_get_all_admins(request: Request):
    """Get all admin accounts"""
    admin = await get_admin_from_token(request)
    
    if not admin.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    admins = await db.admins.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
    return {"admins": admins}

@api_router.post("/admin/admins")
async def admin_create_admin(request: Request, data: AdminCreate):
    """Create a new admin account"""
    admin = await get_admin_from_token(request)
    
    if not admin.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    # Check if email already exists
    existing = await db.admins.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_admin = {
        "id": str(uuid.uuid4()),
        "email": data.email,
        "username": data.username,
        "password_hash": hash_password(data.password),
        "role": data.role,
        "is_super_admin": data.role == "super_admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None
    }
    
    await db.admins.insert_one(new_admin)
    new_admin.pop("_id", None)
    await log_admin_activity(admin['id'], admin['email'], "create_admin", "admin", new_admin['id'], f"Role: {data.role}")
    
    new_admin.pop("password_hash")
    return {"admin": new_admin, "message": "Admin created"}

@api_router.delete("/admin/admins/{admin_id}")
async def admin_delete_admin(request: Request, admin_id: str):
    """Delete an admin account"""
    admin = await get_admin_from_token(request)
    
    if not admin.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    if admin['id'] == admin_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.admins.delete_one({"id": admin_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    await log_admin_activity(admin['id'], admin['email'], "delete_admin", "admin", admin_id)
    
    return {"message": "Admin deleted"}

@api_router.put("/admin/admins/{admin_id}/role")
async def admin_update_admin_role(request: Request, admin_id: str, role: str):
    """Update an admin's role"""
    admin = await get_admin_from_token(request)
    
    if not admin.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    is_super = role == "super_admin"
    result = await db.admins.update_one({"id": admin_id}, {"$set": {"role": role, "is_super_admin": is_super}})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    await log_admin_activity(admin['id'], admin['email'], "update_admin_role", "admin", admin_id, f"New role: {role}")
    
    return {"message": "Admin role updated"}

# ============ 8. ACTIVITY LOGS ============

@api_router.get("/admin/activity-logs")
async def admin_get_activity_logs(request: Request, skip: int = 0, limit: int = 100, action: str = None, admin_id: str = None):
    """Get admin activity logs"""
    admin = await get_admin_from_token(request)
    
    query = {}
    if action:
        query["action"] = action
    if admin_id:
        query["admin_id"] = admin_id
    
    logs = await db.admin_activity_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.admin_activity_logs.count_documents(query)
    
    return {"logs": logs, "total": total}

@api_router.get("/admin/activity-logs/summary")
async def admin_get_activity_summary(request: Request):
    """Get activity logs summary"""
    admin = await get_admin_from_token(request)
    
    # Actions by type
    actions_pipeline = [
        {"$group": {"_id": "$action", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    actions = await db.admin_activity_logs.aggregate(actions_pipeline).to_list(20)
    
    # Actions by admin
    admins_pipeline = [
        {"$group": {"_id": "$admin_email", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    admin_actions = await db.admin_activity_logs.aggregate(admins_pipeline).to_list(10)
    
    # Recent activity (last 24 hours)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent_count = await db.admin_activity_logs.count_documents({"timestamp": {"$gte": yesterday.isoformat()}})
    
    return {
        "actions_by_type": [{"action": a["_id"], "count": a["count"]} for a in actions],
        "actions_by_admin": [{"admin": a["_id"], "count": a["count"]} for a in admin_actions],
        "recent_activity_count": recent_count,
        "total_logs": await db.admin_activity_logs.count_documents({})
    }

# ============ BLOG ROUTES (SEO FRIENDLY) ============

class BlogPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    excerpt: str
    meta_description: str
    meta_keywords: List[str] = []
    featured_image: Optional[str] = None
    author: str = "Admin"
    category: str = "General"
    tags: List[str] = []
    status: str = "draft"  # draft, published
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    views: int = 0

class BlogPostCreate(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: str
    meta_description: str
    meta_keywords: List[str] = []
    featured_image: Optional[str] = None
    author: str = "Admin"
    category: str = "General"
    tags: List[str] = []
    status: str = "draft"

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[List[str]] = None
    featured_image: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None

# Public blog routes (for SEO - no auth required)
@api_router.get("/blog/posts")
async def get_blog_posts(
    page: int = 1,
    limit: int = 10,
    category: Optional[str] = None,
    tag: Optional[str] = None
):
    """Get published blog posts with pagination (public endpoint)"""
    query = {"status": "published"}
    if category:
        query["category"] = category
    if tag:
        query["tags"] = tag
    
    skip = (page - 1) * limit
    posts = await db.blog_posts.find(query, {"_id": 0, "content": 0}).sort("published_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.blog_posts.count_documents(query)
    
    return {
        "posts": posts,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.get("/blog/posts/{slug}")
async def get_blog_post_by_slug(slug: str):
    """Get a single blog post by slug (public endpoint)"""
    post = await db.blog_posts.find_one({"slug": slug, "status": "published"}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Increment view count
    await db.blog_posts.update_one({"slug": slug}, {"$inc": {"views": 1}})
    
    return post

@api_router.get("/blog/categories")
async def get_blog_categories():
    """Get all blog categories with post counts"""
    pipeline = [
        {"$match": {"status": "published"}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    categories = await db.blog_posts.aggregate(pipeline).to_list(50)
    return {"categories": [{"name": c["_id"], "count": c["count"]} for c in categories]}

@api_router.get("/blog/tags")
async def get_blog_tags():
    """Get all blog tags"""
    pipeline = [
        {"$match": {"status": "published"}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 30}
    ]
    tags = await db.blog_posts.aggregate(pipeline).to_list(30)
    return {"tags": [{"name": t["_id"], "count": t["count"]} for t in tags]}

@api_router.get("/blog/related/{slug}")
async def get_related_posts(slug: str, limit: int = 3):
    """Get related blog posts based on category and tags"""
    current_post = await db.blog_posts.find_one({"slug": slug}, {"_id": 0})
    if not current_post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Find posts with similar category or tags
    query = {
        "status": "published",
        "slug": {"$ne": slug},
        "$or": [
            {"category": current_post.get("category")},
            {"tags": {"$in": current_post.get("tags", [])}}
        ]
    }
    
    related = await db.blog_posts.find(query, {"_id": 0, "content": 0}).sort("views", -1).limit(limit).to_list(limit)
    return {"related": related}

# Admin blog routes (protected)
@api_router.get("/admin/blog/posts")
async def admin_get_all_blog_posts(request: Request, page: int = 1, limit: int = 20):
    """Get all blog posts including drafts (admin only)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    skip = (page - 1) * limit
    posts = await db.blog_posts.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.blog_posts.count_documents({})
    
    return {
        "posts": posts,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.get("/admin/blog/posts/{post_id}")
async def admin_get_blog_post(request: Request, post_id: str):
    """Get a single blog post by ID (admin only)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    post = await db.blog_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    return post

@api_router.post("/admin/blog/posts")
async def create_blog_post(request: Request, post_data: BlogPostCreate):
    """Create a new blog post (admin only)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    # Check for duplicate slug
    existing = await db.blog_posts.find_one({"slug": post_data.slug})
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists")
    
    now = datetime.now(timezone.utc)
    post = {
        "id": str(uuid.uuid4()),
        "title": post_data.title,
        "slug": post_data.slug,
        "content": post_data.content,
        "excerpt": post_data.excerpt,
        "meta_description": post_data.meta_description,
        "meta_keywords": post_data.meta_keywords,
        "featured_image": post_data.featured_image,
        "author": post_data.author,
        "category": post_data.category,
        "tags": post_data.tags,
        "status": post_data.status,
        "published_at": now.isoformat() if post_data.status == "published" else None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "views": 0
    }
    
    await db.blog_posts.insert_one(post)
    post.pop("_id", None)
    
    return {"post": post, "message": "Blog post created successfully"}

@api_router.put("/admin/blog/posts/{post_id}")
async def update_blog_post(request: Request, post_id: str, update_data: BlogPostUpdate):
    """Update a blog post (admin only)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    existing = await db.blog_posts.find_one({"id": post_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Check for slug conflict if changing slug
    if update_data.slug and update_data.slug != existing.get("slug"):
        conflict = await db.blog_posts.find_one({"slug": update_data.slug, "id": {"$ne": post_id}})
        if conflict:
            raise HTTPException(status_code=400, detail="A post with this slug already exists")
    
    updates = {k: v for k, v in update_data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Set published_at if status changed to published
    if update_data.status == "published" and existing.get("status") != "published":
        updates["published_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.blog_posts.update_one({"id": post_id}, {"$set": updates})
    
    updated = await db.blog_posts.find_one({"id": post_id}, {"_id": 0})
    return {"post": updated, "message": "Blog post updated successfully"}

@api_router.delete("/admin/blog/posts/{post_id}")
async def delete_blog_post(request: Request, post_id: str):
    """Delete a blog post (admin only)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(" ")[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    result = await db.blog_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    return {"message": "Blog post deleted successfully"}

# Sitemap endpoint for SEO
@api_router.get("/sitemap.xml")
async def get_sitemap():
    """Generate sitemap XML for SEO"""
    from fastapi.responses import Response as XMLResponse
    
    posts = await db.blog_posts.find({"status": "published"}, {"_id": 0, "slug": 1, "updated_at": 1}).to_list(1000)
    
    base_url = os.environ.get('SITE_URL', 'https://example.com')
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Add homepage
    xml_content += f'  <url><loc>{base_url}/</loc><priority>1.0</priority></url>\n'
    xml_content += f'  <url><loc>{base_url}/blog</loc><priority>0.9</priority></url>\n'
    
    # Add blog posts
    for post in posts:
        xml_content += f'  <url>\n'
        xml_content += f'    <loc>{base_url}/blog/{post["slug"]}</loc>\n'
        xml_content += f'    <lastmod>{post.get("updated_at", "")[:10]}</lastmod>\n'
        xml_content += f'    <priority>0.8</priority>\n'
        xml_content += f'  </url>\n'
    
    xml_content += '</urlset>'
    
    return XMLResponse(content=xml_content, media_type="application/xml")

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()