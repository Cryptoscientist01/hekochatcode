import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Heart, User } from "lucide-react";
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
      {/* Fixed Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-3 flex justify-between items-center">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <Heart className="w-7 h-7 text-primary" fill="#FF0080" />
            <span className="text-xl font-heading font-bold">Candy AI</span>
          </button>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5">
              <User className="w-4 h-4 text-primary" />
              <span className="text-sm text-text-secondary">{user.username}</span>
            </div>
            <Button
              data-testid="logout-btn"
              onClick={onLogout}
              variant="ghost"
              className="text-text-secondary hover:text-white hover:bg-white/10 rounded-full"
            >
              Logout
            </Button>
          </div>
        </div>

        {/* Category Tabs */}
        <div className="border-t border-white/5">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex gap-1">
              {["Girls", "Anime", "Guys"].map((category) => (
                <button
                  key={category}
                  data-testid={`category-${category.toLowerCase()}`}
                  onClick={() => handleCategoryChange(category)}
                  className={`px-8 py-4 font-heading font-semibold text-base transition-all relative ${
                    activeCategory === category
                      ? "text-primary"
                      : "text-text-secondary hover:text-white"
                  }`}
                >
                  {category}
                  {activeCategory === category && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-32 px-6 pb-12">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="text-center text-text-secondary py-20">
              <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
              <p className="mt-4">Loading characters...</p>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
            >
              {characters.map((character, index) => (
                <motion.div
                  key={character.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => handleSelectCharacter(character.id)}
                  data-testid={`character-card-${character.id}`}
                  className="relative overflow-hidden rounded-xl cursor-pointer group"
                >
                  {/* Character Image */}
                  <div className="aspect-[3/4] relative bg-background-paper">
                    <img
                      src={character.avatar_url}
                      alt={character.name}
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent opacity-80" />
                  </div>

                  {/* Character Info - Always Visible */}
                  <div className="absolute bottom-0 left-0 right-0 p-4">
                    <div className="flex items-start justify-between mb-1">
                      <div>
                        <h3 className="text-lg font-heading font-bold text-white">{character.name}</h3>
                        <p className="text-xs text-text-secondary">{character.age} • {character.occupation || 'Available'}</p>
                      </div>
                    </div>
                    <p className="text-xs text-text-secondary line-clamp-2 mt-1">
                      {character.description}
                    </p>
                  </div>

                  {/* Hover Border Effect */}
                  <div className="absolute inset-0 border-2 border-primary opacity-0 group-hover:opacity-100 transition-opacity rounded-xl pointer-events-none" 
                       style={{ boxShadow: '0 0 20px rgba(255, 0, 128, 0.3)' }} />
                </motion.div>
              ))}
            </motion.div>
          )}

          {!loading && characters.length === 0 && (
            <div className="text-center text-text-secondary py-20">
              <p>No characters found in this category.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
