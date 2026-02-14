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
    character = await db.characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    chat_id = f"{request.user_id}_{request.character_id}"
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)
    messages.reverse()
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=chat_id,
        system_message=f"You are {character['name']}, age {character['age']}. {character['personality']} Your traits: {', '.join(character['traits'])}. Be warm, engaging, and conversational. Keep responses concise but meaningful."
    )
    chat.with_model("gemini", "gemini-3-flash-preview")
    
    user_message = UserMessage(text=request.message)
    ai_response = await chat.send_message(user_message)
    
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

@api_router.get("/chat/history/{character_id}")
async def get_chat_history(character_id: str, user_id: str):
    chat_id = f"{user_id}_{character_id}"
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    return {"messages": messages}

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
    character = await db.characters.find_one({"id": request.character_id}, {"_id": 0})
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