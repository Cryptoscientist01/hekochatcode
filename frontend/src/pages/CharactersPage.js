import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, User, Sparkles, Smile } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CharactersPage({ user, onLogout }) {
  const navigate = useNavigate();
  const { category: urlCategory } = useParams();
  const [activeCategory, setActiveCategory] = useState(urlCategory || "Girls");
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (urlCategory) {
      setActiveCategory(urlCategory);
    }
  }, [urlCategory]);

  useEffect(() => {
    fetchCharacters();
  }, [activeCategory]);

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

  const handleSelectCharacter = (characterId) => {
    navigate(`/chat/${characterId}`);
  };

  const handleCategoryChange = (category) => {
    setActiveCategory(category);
    navigate(`/characters/${category}`);
  };

  return (
    <div className="min-h-screen bg-background">
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <button 
              onClick={() => navigate('/')}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity group"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center group-hover:scale-105 transition-transform">
                <Heart className="w-6 h-6 text-white" fill="white" />
              </div>
              <span className="text-xl font-heading font-bold">AI Companion</span>
            </button>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl glass-light">
                <User className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-text-secondary">{user.username}</span>
              </div>
              <Button
                data-testid="logout-btn"
                onClick={onLogout}
                variant="ghost"
                className="text-text-secondary hover:text-white hover:bg-white/5 rounded-xl"
              >
                Logout
              </Button>
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
              {characters.length} unique AI personalities ready to chat
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
                  <div className="aspect-[3/4] relative bg-background-paper">
                    <img
                      src={character.avatar_url}
                      alt={character.name}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                    
                    {/* Smile animation on hover */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none">
                      <motion.div
                        initial={{ scale: 0, rotate: -180 }}
                        whileHover={{ scale: 1, rotate: 0 }}
                        className="group-hover:animate-bounce"
                      >
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/90 to-accent-purple/90 flex items-center justify-center backdrop-blur-sm shadow-neon">
                          <Smile className="w-8 h-8 text-white" />
                        </div>
                      </motion.div>
                    </div>
                    
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
