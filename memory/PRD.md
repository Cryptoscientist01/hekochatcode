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
- [x] **Feature**: Added Settings page with fully functional toggles and actions:
  - Appearance: Dark Mode (applies light/dark theme), Compact Mode (reduces UI density), Language selector
  - Notifications & Sound: Push notifications, Sound effects, Voice autoplay toggles
  - Chat Settings: Typing indicator, Auto-save chats, Chat style selector
  - Privacy & Data: Export Data (downloads all user data as JSON), Reset Settings, Clear Chat History, Delete Account
- [x] **UI**: Updated sidebar menu with Subscription, Profile, and Settings buttons
- [x] **Backend**: Added `/api/chat/clear-all` and `/api/users/{id}/delete-account` endpoints
- [x] **Architecture**: Created SettingsContext for global settings management with localStorage persistence
- [x] **Admin Panel**: Complete admin dashboard at `/optimus` with:
  - Admin login (admin@admin.com / admin123)
  - Analytics dashboard showing users, characters, messages, images, favorites stats
  - User registrations chart (last 7 days)
  - Users management tab (search, view, delete users)
  - Characters management tab (default and custom characters)
  - Admin credentials update functionality
  
- [x] **Admin Panel Enhanced Features** (8 new features):
  1. **Content Moderation** - View all chat conversations, view messages, delete chats
  2. **Site Announcements** - Create, edit, delete site-wide announcements with types (info/warning/success/error)
  3. **Chat Analytics** - Most active users, most popular characters, message trends by day/hour
  4. **Character Editor** - Edit any character's name, age, personality, description, occupation
  5. **User Notifications** - Send notifications to specific users or broadcast to all
  6. **Revenue Dashboard** - Monthly/annual revenue, subscription breakdown (MOCKED - ready for Stripe)
  7. **Admin Roles** - Create/delete admin accounts with roles (super_admin, admin, moderator)
  8. **Activity Logs** - Track all admin actions with timestamps, summaries, and filtering
- [x] **SEO Blog System**: Complete blog feature with:
  - Public blog at `/blog` with post listing, pagination, search
  - Individual post pages at `/blog/{slug}` with SEO meta tags
  - Category and tag filtering
  - Related posts section
  - Social share buttons (Twitter, Facebook, LinkedIn, Copy link)
  - JSON-LD structured data for Google indexing
  - Admin blog manager at `/optimus/blog` for CRUD operations
  - SEO fields: meta description, keywords, featured image
  - Draft/Published status management
  - Sitemap XML endpoint at `/api/sitemap.xml`

- [x] **AI Character Push Notifications**:
  - Service worker for browser push notifications
  - Notification bell icon in header
  - Settings toggle for AI character notifications
  - Flirty message templates (30+ messages)
  - Character prioritization: chatted with > favorites > random
  - Frequency settings: low (1-2/day), medium (3-5/day), high (5+/day)
  - Quiet hours: 10PM-8AM by default
  - Inactivity detection (4+ hours)
  - Notification history tracking
  - Backend endpoints for push subscription, preferences, generation
  - **Automatic Notification Scheduler**: APScheduler running in backend:
    - Random notifications every 2 hours
    - Inactivity notifications every 4 hours
    - VAPID keys configured for real push delivery

- [x] **Multi-Payment Gateway System**:
  - Stripe integration using emergentintegrations library (WORKING)
  - PayPal integration (DEMO/MOCK mode - requires user confirmation)
  - Subscription plans: Free, Premium ($9.99/month or $59.99/year), Ultimate ($19.99/month or $119.99/year)
  - Payment method toggle (Stripe/PayPal) on subscription page
  - Billing cycle toggle (Monthly/Yearly)
  - Checkout session creation with transaction tracking
  - Payment success page with confetti animation
  - User subscription status tracking
  - Payment history endpoint
  - Webhook handler for Stripe events

### Key Push Notification API Endpoints
- `GET /api/push/vapid-public-key` - Get VAPID key for push subscription
- `POST /api/push/subscribe` - Subscribe to push notifications
- `POST /api/push/unsubscribe` - Unsubscribe from notifications
- `GET/PUT /api/push/preferences/{user_id}` - Get/update notification preferences
- `POST /api/push/update-activity` - Update user activity timestamp
- `GET /api/push/generate-notification/{user_id}` - Generate a notification for user
- `GET /api/push/check-inactivity` - Get list of inactive users
- `GET /api/push/notification-history/{user_id}` - Get sent notification history

### Key Admin API Endpoints (New)
- `GET /api/admin/analytics/chats` - Chat analytics (active users, popular characters)
- `GET /api/admin/analytics/revenue` - Revenue dashboard (MOCKED)
- `GET /api/admin/chats` - Get all chats for moderation
- `GET /api/admin/chats/{id}/messages` - Get messages in a chat
- `DELETE /api/admin/chats/{id}` - Delete entire chat
- `POST /api/admin/chats/flag` - Flag a chat for review
- `GET/POST/PUT/DELETE /api/admin/announcements` - CRUD announcements
- `GET/POST /api/admin/notifications` - Get/send notifications
- `GET/POST/DELETE /api/admin/admins` - Manage admin accounts
- `PUT /api/admin/admins/{id}/role` - Update admin role
- `GET /api/admin/activity-logs` - Get activity logs
- `GET /api/admin/activity-logs/summary` - Get activity summary
- `PUT /api/admin/characters/{id}` - Edit character details
- `GET /api/announcements/active` - Public active announcements
- `GET /api/notifications/{user_id}` - Get user notifications

### Key Blog API Endpoints
- `GET /api/blog/posts` - Get published posts (public)
- `GET /api/blog/posts/{slug}` - Get single post by slug (public)
- `GET /api/blog/categories` - Get categories with counts (public)
- `GET /api/blog/tags` - Get popular tags (public)
- `GET /api/blog/related/{slug}` - Get related posts (public)
- `POST /api/admin/blog/posts` - Create post (admin)
- `PUT /api/admin/blog/posts/{id}` - Update post (admin)
- `DELETE /api/admin/blog/posts/{id}` - Delete post (admin)
- `GET /api/sitemap.xml` - XML sitemap for SEO

### Backlog (P1)
- [ ] Stripe integration for Premium subscription payments
- [ ] Voice Interaction (TTS) - Read AI messages aloud with voice button

### Backlog (P2)
- [ ] Internationalization (i18n) for multi-language UI
- [ ] Advanced voice selection per character
- [ ] Chat export functionality

### Future Features (P3)
- [ ] Character relationship progression
- [ ] More character categories
- [ ] Message reactions/emotions
