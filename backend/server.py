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

# Helper function to hash passwords
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    return jwt.encode({"user_id": user_id}, JWT_SECRET, algorithm="HS256")

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