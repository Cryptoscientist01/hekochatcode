import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, User, Sparkles, MessageCircle, ChevronDown, Clock, Menu, Home, Compass, Image as ImageIcon, Wand2, HeartHandshake, Crown, X, FolderHeart, LogOut, Settings, CreditCard, Bell } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { toast } from "sonner";
import NotificationPrompt, { NotificationBell } from "@/components/NotificationPrompt";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CharactersPage({ user, onLogout }) {
  const navigate = useNavigate();
  const { category: urlCategory } = useParams();
  const [activeCategory, setActiveCategory] = useState(urlCategory || "Girls");
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showChatsDropdown, setShowChatsDropdown] = useState(false);
  const [showSideMenu, setShowSideMenu] = useState(false);
  const [myChats, setMyChats] = useState([]);
  const [loadingChats, setLoadingChats] = useState(false);
  const dropdownRef = useRef(null);
  const sideMenuRef = useRef(null);
  
  // Get token from localStorage
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (urlCategory) {
      setActiveCategory(urlCategory);
    }
  }, [urlCategory]);

  useEffect(() => {
    fetchCharacters();
  }, [activeCategory]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowChatsDropdown(false);
      }
      if (sideMenuRef.current && !sideMenuRef.current.contains(event.target)) {
        setShowSideMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchCharacters = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/characters?category=${activeCategory}`);
      setCharacters(response.data);
    } catch (error) {
      toast.error("Failed to load characters");
    } finally {
      setLoading(false);
    }
  };

  const fetchMyChats = async () => {
    if (myChats.length > 0) return; // Already loaded
    setLoadingChats(true);
    try {
      const response = await axios.get(`${API}/chat/my-chats?user_id=${user.id}`);
      setMyChats(response.data.chats || []);
    } catch (error) {
      console.error("Failed to load chats", error);
    } finally {
      setLoadingChats(false);
    }
  };

  const handleToggleChatsDropdown = () => {
    const newState = !showChatsDropdown;
    setShowChatsDropdown(newState);
    if (newState) {
      fetchMyChats();
    }
  };

  const handleSelectCharacter = (characterId) => {
    navigate(`/chat/${characterId}`);
  };

  const handleCategoryChange = (category) => {
    setActiveCategory(category);
    navigate(`/characters/${category}`);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Side Menu Overlay */}
      <AnimatePresence>
        {showSideMenu && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-50"
              onClick={() => setShowSideMenu(false)}
            />
            <motion.div
              ref={sideMenuRef}
              initial={{ x: -300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -300, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed top-0 left-0 h-full w-72 glass-heavy border-r border-white/10 z-50 flex flex-col"
            >
              {/* Menu Header */}
              <div className="p-6 border-b border-white/10 flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center">
                    <Heart className="w-6 h-6 text-white" fill="white" />
                  </div>
                  <span className="text-xl font-heading font-bold">AI Companion</span>
                </div>
                <button
                  onClick={() => setShowSideMenu(false)}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Menu Items - Scrollable */}
              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                <button
                  data-testid="menu-home"
                  onClick={() => { navigate('/'); setShowSideMenu(false); }}
                  className="w-full flex items-center gap-4 px-4 py-4 rounded-xl hover:bg-white/10 transition-all text-left group"
                >
                  <Home className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                  <span className="font-medium">Home</span>
                </button>

                <button
                  data-testid="menu-discover"
                  onClick={() => { navigate('/characters'); setShowSideMenu(false); }}
                  className="w-full flex items-center gap-4 px-4 py-4 rounded-xl bg-white/5 border border-white/10 text-left group"
                >
                  <Compass className="w-5 h-5 text-primary" />
                  <span className="font-medium text-primary">Discover</span>
                </button>

                <button
                  data-testid="menu-chat"
                  onClick={() => { handleToggleChatsDropdown(); }}
                  className="w-full flex items-center gap-4 px-4 py-4 rounded-xl hover:bg-white/10 transition-all text-left group"
                >
                  <MessageCircle className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                  <span className="font-medium">Chat</span>
                  <ChevronDown className={`w-4 h-4 ml-auto transition-transform ${showChatsDropdown ? 'rotate-180' : ''}`} />
                </button>

                {/* Chat submenu */}
                <AnimatePresence>
                  {showChatsDropdown && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden ml-4"
                    >
                      {loadingChats ? (
                        <div className="p-4 text-center text-text-secondary">
                          <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
                        </div>
                      ) : myChats.length === 0 ? (
                        <div className="p-4 text-sm text-text-secondary">No conversations yet</div>
                      ) : (
                        myChats.slice(0, 5).map((chat) => (
                          <button
                            key={chat.character_id}
                            onClick={() => { navigate(`/chat/${chat.character_id}`); setShowSideMenu(false); }}
                            className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors"
                          >
                            <img src={chat.character_avatar} alt={chat.character_name} className="w-8 h-8 rounded-full object-cover" />
                            <span className="text-sm truncate">{chat.character_name}</span>
                          </button>
                        ))
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                <button
                  data-testid="menu-collection"
                  onClick={() => { navigate('/collection'); setShowSideMenu(false); }}
                  className="w-full flex items-center gap-4 px-4 py-4 rounded-xl hover:bg-white/10 transition-all text-left group"
                >
                  <FolderHeart className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                  <span className="font-medium">Collection</span>
                </button>

                <button
                  data-testid="menu-generate-image"
                  onClick={() => { navigate('/generate-image'); setShowSideMenu(false); }}
                  className="w-full flex items-center gap-4 px-4 py-4 rounded-xl hover:bg-white/10 transition-all text-left group"
                >
                  <ImageIcon className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                  <span className="font-medium">Generate Image</span>
                </button>

                <button
                  data-testid="menu-create-character"
                  onClick={() => { navigate('/create-character'); setShowSideMenu(false); }}
                  className="w-full flex items-center gap-4 px-4 py-4 rounded-xl hover:bg-white/10 transition-all text-left group"
                >
                  <Wand2 className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                  <span className="font-medium">Create Character</span>
                </button>

                <button
                  data-testid="menu-my-ai"
                  onClick={() => { navigate('/my-ai'); setShowSideMenu(false); }}
                  className="w-full flex items-center gap-4 px-4 py-4 rounded-xl hover:bg-white/10 transition-all text-left group"
                >
                  <HeartHandshake className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                  <span className="font-medium">My AI</span>
                </button>

                {/* Divider and Premium/Account Section */}
                <div className="pt-4 border-t border-white/10 mt-4 space-y-2">
                  <button
                    data-testid="menu-subscription"
                    onClick={() => { navigate('/subscription'); setShowSideMenu(false); }}
                    className="w-full flex items-center gap-4 px-4 py-4 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 hover:from-amber-500/30 hover:to-orange-500/30 transition-all text-left group"
                  >
                    <Crown className="w-5 h-5 text-amber-400" />
                    <span className="font-medium text-amber-400">Subscription</span>
                    <span className="ml-auto px-2 py-1 bg-red-500 text-white text-xs font-bold rounded-full">50% OFF</span>
                  </button>

                  <button
                    data-testid="menu-profile"
                    onClick={() => { navigate('/profile'); setShowSideMenu(false); }}
                    className="w-full flex items-center gap-4 px-4 py-4 rounded-xl hover:bg-white/10 transition-all text-left group"
                  >
                    <User className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                    <span className="font-medium">Profile</span>
                  </button>

                  <button
                    data-testid="menu-settings"
                    onClick={() => { navigate('/settings'); setShowSideMenu(false); }}
                    className="w-full flex items-center gap-4 px-4 py-4 rounded-xl hover:bg-white/10 transition-all text-left group"
                  >
                    <Settings className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                    <span className="font-medium">Settings</span>
                  </button>
                </div>
              </div>

              {/* User Info at Bottom - Fixed */}
              <div className="flex-shrink-0 p-4 border-t border-white/10 glass-heavy">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{user.username || user.name || user.email}</p>
                    <p className="text-xs text-text-secondary truncate">{user.email}</p>
                  </div>
                </div>
                <Button
                  data-testid="menu-logout"
                  onClick={() => { onLogout(); setShowSideMenu(false); }}
                  variant="ghost"
                  className="w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <nav className="fixed top-0 w-full z-40 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              {/* Hamburger Menu Button */}
              <button
                data-testid="hamburger-menu-btn"
                onClick={() => setShowSideMenu(true)}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              >
                <Menu className="w-6 h-6" />
              </button>

              <button 
                onClick={() => navigate('/')}
                className="flex items-center gap-3 hover:opacity-80 transition-opacity group"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center group-hover:scale-105 transition-transform">
                  <Heart className="w-6 h-6 text-white" fill="white" />
                </div>
                <span className="text-xl font-heading font-bold hidden sm:block">AI Companion</span>
              </button>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-xl glass-light">
                <User className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-text-secondary">{user.username || user.name || user.email}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-white/5">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex gap-2">
              {["Girls", "Anime", "Guys"].map((category) => (
                <button
                  key={category}
                  data-testid={`category-${category.toLowerCase()}`}
                  onClick={() => handleCategoryChange(category)}
                  className={`px-8 py-5 font-heading font-semibold text-base transition-all relative ${
                    activeCategory === category
                      ? "text-white"
                      : "text-text-muted hover:text-text-secondary"
                  }`}
                >
                  {category}
                  {activeCategory === category && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary to-accent-purple"
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      </nav>

      <div className="pt-36 px-6 pb-16">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12 text-center"
          >
            <h1 className="text-4xl md:text-5xl font-heading font-bold mb-4">
              {activeCategory} <span className="text-primary">Characters</span>
            </h1>
            <p className="text-text-secondary text-lg">
              Unique AI personalities ready to chat
            </p>
          </motion.div>

          {loading ? (
            <div className="text-center text-text-secondary py-20">
              <div className="inline-block w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-lg">Loading characters...</p>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6"
            >
              {characters.map((character, index) => (
                <motion.div
                  key={character.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.03 }}
                  onClick={() => handleSelectCharacter(character.id)}
                  data-testid={`character-card-${character.id}`}
                  className="relative overflow-hidden rounded-2xl cursor-pointer group shadow-card hover:shadow-card-hover transition-all duration-300"
                  whileHover={{ y: -8 }}
                >
                  <div className="aspect-[3/4] relative bg-background-paper overflow-hidden">
                    <motion.img
                      src={character.avatar_url}
                      alt={character.name}
                      className="w-full h-full object-cover"
                      whileHover={{ 
                        scale: 1.1,
                        rotate: [0, -2, 2, -2, 0],
                        transition: { 
                          rotate: { repeat: Infinity, duration: 0.5, ease: "easeInOut" },
                          scale: { duration: 0.3 }
                        }
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                    
                    <div className="absolute top-3 right-3 flex gap-2">
                      <div className="px-3 py-1.5 rounded-full glass-heavy text-xs font-semibold backdrop-blur-xl">
                        {character.age}
                      </div>
                    </div>

                    <div className="absolute top-3 left-3">
                      <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full glass-heavy backdrop-blur-xl">
                        <div className="w-2 h-2 rounded-full bg-status-online animate-pulse"></div>
                        <span className="text-xs font-medium">Online</span>
                      </div>
                    </div>
                  </div>

                  <div className="absolute bottom-0 left-0 right-0 p-5">
                    <h3 className="text-lg font-heading font-bold text-white mb-1">{character.name}</h3>
                    <p className="text-xs text-text-secondary mb-2">{character.occupation || 'Available to Chat'}</p>
                    <p className="text-sm text-text-secondary line-clamp-2 leading-relaxed">
                      {character.description}
                    </p>
                    
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {character.traits.slice(0, 2).map((trait) => (
                        <span
                          key={trait}
                          className="px-2 py-1 rounded-lg bg-primary/10 border border-primary/20 text-xs font-medium text-primary"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="absolute inset-0 border-2 border-primary opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl pointer-events-none" 
                       style={{ boxShadow: '0 0 30px rgba(255, 0, 128, 0.4)' }} />
                  
                  <div className="absolute inset-0 bg-gradient-to-t from-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                </motion.div>
              ))}
            </motion.div>
          )}

          {!loading && characters.length === 0 && (
            <div className="text-center text-text-secondary py-20">
              <Sparkles className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No characters found in this category.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
