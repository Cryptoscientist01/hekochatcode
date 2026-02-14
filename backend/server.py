from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import bcrypt
import jwt
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
    personality: str
    traits: List[str]
    category: str
    avatar_url: str
    description: str

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

# Initialize default characters on startup
async def init_characters():
    existing = await db.characters.count_documents({})
    if existing == 0:
        default_characters = [
            {
                "id": str(uuid.uuid4()),
                "name": "Luna",
                "personality": "Sweet, caring, and loves deep conversations. Luna enjoys poetry and stargazing.",
                "traits": ["Romantic", "Intellectual", "Caring"],
                "category": "Casual",
                "avatar_url": "https://images.unsplash.com/photo-1607332646791-929f9ddcf96a?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "A gentle soul who loves meaningful connections"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Aria",
                "personality": "Artistic and creative. Aria is passionate about music and visual arts. She's expressive and free-spirited.",
                "traits": ["Creative", "Expressive", "Passionate"],
                "category": "Artistic",
                "avatar_url": "https://images.unsplash.com/photo-1561450863-83d1391238bb?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "An artistic spirit who sees beauty everywhere"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Sakura",
                "personality": "Traditional yet modern. Sakura values culture and family. She's kind and respectful.",
                "traits": ["Traditional", "Respectful", "Kind"],
                "category": "Cultural",
                "avatar_url": "https://images.unsplash.com/photo-1768017093006-6a67c794d512?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "A blend of tradition and modernity"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Nova",
                "personality": "Bold and adventurous. Nova loves trying new things and living on the edge. She's confident and playful.",
                "traits": ["Adventurous", "Bold", "Playful"],
                "category": "Edgy",
                "avatar_url": "https://images.unsplash.com/photo-1576348076752-6085814e5a51?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "A daring soul who lives life to the fullest"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Emma",
                "personality": "Professional and ambitious. Emma is career-focused but knows how to have fun. She's smart and witty.",
                "traits": ["Professional", "Ambitious", "Witty"],
                "category": "Professional",
                "avatar_url": "https://images.unsplash.com/photo-1629350260660-6053fe4fcf47?crop=entropy&cs=srgb&fm=jpg&q=85",
                "description": "Success-driven with a playful side"
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
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
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
async def get_characters():
    characters = await db.characters.find({}, {"_id": 0}).to_list(100)
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
    # Get character
    character = await db.characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get chat history for context
    chat_id = f"{request.user_id}_{request.character_id}"
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)
    messages.reverse()
    
    # Create AI chat instance
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=chat_id,
        system_message=f"You are {character['name']}, an AI girlfriend. {character['personality']} Your traits: {', '.join(character['traits'])}. Be warm, engaging, and conversational. Keep responses concise but meaningful."
    )
    chat.with_model("gemini", "gemini-3-flash-preview")
    
    # Send message to AI
    user_message = UserMessage(text=request.message)
    ai_response = await chat.send_message(user_message)
    
    # Save user message
    user_msg = Message(
        chat_id=chat_id,
        sender="user",
        content=request.message
    )
    user_msg_dict = user_msg.model_dump()
    user_msg_dict['timestamp'] = user_msg_dict['timestamp'].isoformat()
    await db.messages.insert_one(user_msg_dict)
    
    # Save AI message
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
        
        # Convert to base64 for easy transmission
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {"audio": audio_base64, "format": "mp3"}
    except Exception as e:
        logging.error(f"Voice generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Image Routes
@api_router.post("/image/generate")
async def generate_image(request: ImageGenerateRequest):
    # Get character for context
    character = await db.characters.find_one({"id": request.character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Create enhanced prompt
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
            # Return first image
            return {
                "image": images[0]['data'],
                "mime_type": images[0]['mime_type']
            }
        else:
            raise HTTPException(status_code=500, detail="No image generated")
    except Exception as e:
        logging.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()