# AI Companion Web App - Product Requirements Document

## Original Problem Statement
Build a fully functional AI companion web app similar to candy.ai with features for text chat, voice interaction, and image generation. The app should have 20+ unique avatars categorized into "Girls", "Anime", and "Guys".

## User Personas
- Users seeking AI companionship and conversation
- Users interested in personalized AI interactions with diverse character personalities
- Users who want voice and visual interactions beyond text chat

## Core Requirements
1. **Character Selection**: 25+ unique AI characters across 3 categories (Girls, Anime, Guys)
2. **Authentication**: Google OAuth + Traditional email/password auth
3. **Text Chat**: Real-time AI conversations using Gemini 3 Flash
4. **Voice Generation**: Text-to-speech for AI responses using OpenAI TTS
5. **Image Generation**: AI-generated images using Gemini Nano Banana
6. **Favorites/Collection**: Save and manage favorite characters
7. **Custom Characters**: Create your own AI companions
8. **Standalone Image Generation**: Generate images from text prompts

## Technical Architecture
```
/app/
├── backend/
│   ├── .env (MONGO_URL, DB_NAME, EMERGENT_LLM_KEY)
│   ├── requirements.txt
│   └── server.py (FastAPI - All APIs)
└── frontend/
    ├── .env (REACT_APP_BACKEND_URL)
    ├── package.json
    └── src/
        ├── App.js (Routing)
        ├── pages/
        │   ├── LandingPage.js
        │   ├── AuthPage.js
        │   ├── CharactersPage.js (with hamburger menu)
        │   ├── ChatPage.js (with favorite toggle)
        │   ├── CollectionPage.js (favorites)
        │   ├── GenerateImagePage.js
        │   ├── CreateCharacterPage.js
        │   └── MyAIPage.js
        └── components/ui/
```

## Key API Endpoints

### Authentication
- `POST /api/auth/signup` - Email/password registration
- `POST /api/auth/login` - Email/password login  
- `POST /api/auth/google/session` - Google OAuth
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Characters
- `GET /api/characters` - Get all characters (with optional category filter)
- `GET /api/characters/{id}` - Get single character
- `POST /api/characters/create` - Create custom character
- `GET /api/characters/my/{user_id}` - Get user's custom characters
- `GET /api/characters/custom/{id}` - Get single custom character
- `DELETE /api/characters/custom/{id}` - Delete custom character

### Chat
- `POST /api/chat/send` - Send message and get AI response
- `GET /api/chat/history/{character_id}` - Get chat history
- `GET /api/chat/my-chats` - Get user's recent conversations

### Favorites
- `POST /api/favorites/add` - Add to favorites
- `POST /api/favorites/remove` - Remove from favorites
- `GET /api/favorites/{user_id}` - Get all favorites
- `GET /api/favorites/check/{user_id}/{character_id}` - Check if favorited

### Voice & Image
- `POST /api/voice/generate` - Generate voice audio
- `POST /api/image/generate` - Generate image in chat
- `POST /api/images/generate` - Standalone image generation
- `GET /api/images/my/{user_id}` - Get user's generated images
- `DELETE /api/images/{image_id}` - Delete image

## Database Schema (MongoDB)
- **users**: User accounts
- **user_sessions**: Auth sessions
- **characters**: Pre-defined AI characters
- **custom_characters**: User-created characters
- **messages**: Chat messages
- **favorites**: User favorites
- **generated_images**: Standalone generated images

## 3rd Party Integrations
- **Gemini 3 Flash** - Text generation (via EMERGENT_LLM_KEY)
- **OpenAI TTS** - Voice synthesis (via EMERGENT_LLM_KEY)
- **Gemini Nano Banana** - Image generation (via EMERGENT_LLM_KEY)
- **Emergent-managed Google Auth** - Social login

---

## Implementation Status

### Completed (December 2025)
- [x] Project setup (React + FastAPI + MongoDB)
- [x] Professional UI with dark theme
- [x] 25+ characters (Girls, Anime, Guys)
- [x] Google OAuth + Email/password auth
- [x] AI chat with Gemini 3 Flash
- [x] Voice generation with OpenAI TTS
- [x] Image generation in chat
- [x] Hamburger menu with full navigation
- [x] **Collection/Favorites system**
- [x] **Create Custom Character page**
- [x] **My AI page (user's creations)**
- [x] **Standalone Generate Image page**
- [x] Favorite toggle on chat page
- [x] Testing (100% pass rate)

### Completed (February 2026)
- [x] **Bug Fix**: Chat with custom characters now working (fixed `/api/chat/send` to check both `characters` and `custom_characters` collections)
- [x] **Bug Fix**: Image generation in chat with custom characters now working (same fix for `/api/image/generate`)
- [x] **UI Fix**: Removed character count from "My AI Characters" page
- [x] **Feature**: Added Subscription page with 3 pricing tiers (Free, Premium, Ultimate), billing toggle, feature comparison
- [x] **Feature**: Added Profile page with user stats, avatar, subscription badge, quick actions
- [x] **Feature**: Added Settings page with toggles for appearance, notifications, sound, chat preferences, privacy/data options
- [x] **UI**: Updated sidebar menu with Subscription, Profile, and Settings buttons

### Backlog (P2)
- [ ] Premium subscription features
- [ ] Advanced voice selection per character
- [ ] Chat export functionality

### Future Features (P3)
- [ ] Character relationship progression
- [ ] More character categories
- [ ] Message reactions/emotions
