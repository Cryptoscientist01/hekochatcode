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

## Technical Architecture
```
/app/
├── backend/
│   ├── .env (MONGO_URL, DB_NAME, EMERGENT_LLM_KEY)
│   ├── requirements.txt
│   └── server.py (FastAPI - Auth, Characters, Chat, Voice, Image APIs)
└── frontend/
    ├── .env (REACT_APP_BACKEND_URL)
    ├── package.json
    └── src/
        ├── App.js (Routing + Auth callback handling)
        ├── pages/
        │   ├── LandingPage.js (Homepage with character showcase)
        │   ├── AuthPage.js (Google + Email/Password auth)
        │   ├── CharactersPage.js (Character grid with category filter)
        │   └── ChatPage.js (Chat interface with voice/image features)
        └── components/ui/ (Shadcn components)
```

## Key API Endpoints
- `POST /api/auth/signup` - Email/password registration
- `POST /api/auth/login` - Email/password login  
- `POST /api/auth/google/session` - Google OAuth session exchange
- `GET /api/auth/me` - Get current authenticated user
- `POST /api/auth/logout` - Logout and clear session
- `GET /api/characters` - Get all characters (with optional category filter)
- `GET /api/characters/{id}` - Get single character
- `POST /api/chat/send` - Send message and get AI response
- `GET /api/chat/history/{character_id}` - Get chat history
- `POST /api/voice/generate` - Generate voice audio from text
- `POST /api/image/generate` - Generate image from prompt

## Database Schema (MongoDB)
- **users**: `{id, user_id, email, username, name, picture, password_hash?, auth_provider, created_at}`
- **user_sessions**: `{user_id, session_token, expires_at, created_at}`
- **characters**: `{id, name, age, personality, traits, category, avatar_url, description, occupation}`
- **messages**: `{id, chat_id, sender, content, timestamp}`

## 3rd Party Integrations
- **Gemini 3 Flash** - Text generation for AI chat (via EMERGENT_LLM_KEY)
- **OpenAI TTS** - Voice synthesis for AI responses (via EMERGENT_LLM_KEY)
- **Gemini Nano Banana** - Image generation (via EMERGENT_LLM_KEY)
- **Emergent-managed Google Auth** - Social login

---

## Implementation Status

### Completed (December 2025)
- [x] Project setup with React frontend + FastAPI backend + MongoDB
- [x] Professional UI design with dark theme and glassmorphism
- [x] Homepage with character showcase and category switcher
- [x] 25 unique characters (10 Girls, 8 Anime, 7 Guys) with images and bios
- [x] Traditional email/password authentication (signup + login)
- [x] Google OAuth authentication via Emergent Auth
- [x] Character listing with category filtering
- [x] Chat page with message UI
- [x] AI chat integration with Gemini 3 Flash
- [x] Voice generation integration with OpenAI TTS
- [x] Image generation integration with Gemini Nano Banana
- [x] Chat history persistence
- [x] Comprehensive testing (100% pass rate)

### Backlog (P1 - Next Up)
- [ ] User profile page with settings
- [ ] Character favorites/bookmarks

### Future Features (P2)
- [ ] Character builder - let users create custom AI characters
- [ ] Advanced voice selection (multiple voices per character)
- [ ] Chat export functionality
- [ ] Message reactions/emotions

### Enhancements (P3)
- [ ] Premium subscription features
- [ ] More character categories
- [ ] Character relationship progression system
