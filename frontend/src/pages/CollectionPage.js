import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Heart, ArrowLeft, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CollectionPage({ user, onLogout }) {
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/favorites/${user.id}`);
      setFavorites(response.data.favorites || []);
    } catch (error) {
      toast.error("Failed to load favorites");
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (characterId) => {
    try {
      await axios.post(`${API}/favorites/remove`, {
        user_id: user.id,
        character_id: characterId
      });
      setFavorites(favorites.filter(f => f.id !== characterId));
      toast.success("Removed from collection");
    } catch (error) {
      toast.error("Failed to remove from collection");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => navigate('/characters')}
                variant="ghost"
                className="text-text-secondary hover:text-white"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Back
              </Button>
              <h1 className="text-xl font-heading font-bold">My Collection</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-heading font-bold mb-4">
              Your <span className="text-primary">Favorites</span>
            </h2>
            <p className="text-text-secondary">
              {favorites.length} character{favorites.length !== 1 ? 's' : ''} saved
            </p>
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : favorites.length === 0 ? (
            <div className="text-center py-20">
              <Heart className="w-16 h-16 text-text-muted mx-auto mb-4" />
              <h3 className="text-xl font-heading font-bold mb-2">No favorites yet</h3>
              <p className="text-text-secondary mb-6">Start adding characters to your collection!</p>
              <Button
                onClick={() => navigate('/characters')}
                className="bg-primary hover:bg-primary/90"
              >
                Browse Characters
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
              {favorites.map((character, index) => (
                <motion.div
                  key={character.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="relative overflow-hidden rounded-2xl cursor-pointer group shadow-card hover:shadow-card-hover transition-all duration-300"
                >
                  <div 
                    className="aspect-[3/4] relative bg-background-paper"
                    onClick={() => navigate(`/chat/${character.id}`)}
                  >
                    <motion.img
                      src={character.avatar_url}
                      alt={character.name}
                      className="w-full h-full object-cover"
                      whileHover={{ scale: 1.1 }}
                      transition={{ duration: 0.3 }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                    
                    {/* Remove Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveFavorite(character.id);
                      }}
                      className="absolute top-3 right-3 p-2 rounded-full glass-heavy opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/20"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>

                    <div className="absolute top-3 left-3">
                      <Heart className="w-5 h-5 text-primary" fill="#FF0080" />
                    </div>
                  </div>

                  <div className="absolute bottom-0 left-0 right-0 p-4">
                    <h3 className="text-lg font-heading font-bold text-white mb-1">{character.name}</h3>
                    <p className="text-xs text-text-secondary">{character.category}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
