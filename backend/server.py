from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response as FastAPIResponse
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.llm.openai import OpenAITextToSpeech
import base64
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

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

@app.on_event("startup")
async def startup_event():
    await init_characters()
    await init_admin()

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