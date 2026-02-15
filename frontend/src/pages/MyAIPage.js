import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Trash2, MessageCircle, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MyAIPage({ user }) {
  const navigate = useNavigate();
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMyCharacters();
  }, []);

  const fetchMyCharacters = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/characters/my/${user.id}`);
      setCharacters(response.data.characters || []);
    } catch (error) {
      toast.error("Failed to load your characters");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (characterId) => {
    if (!window.confirm("Are you sure you want to delete this character?")) return;

    try {
      await axios.delete(`${API}/characters/custom/${characterId}?user_id=${user.id}`);
      setCharacters(characters.filter(c => c.id !== characterId));
      toast.success("Character deleted");
    } catch (error) {
      toast.error("Failed to delete character");
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
              <h1 className="text-xl font-heading font-bold">My AI Characters</h1>
            </div>
            <Button
              onClick={() => navigate('/create-character')}
              className="bg-primary hover:bg-primary/90"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Create New
            </Button>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-heading font-bold mb-4">
              Your <span className="text-primary">Creations</span>
            </h2>
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : characters.length === 0 ? (
            <div className="text-center py-20">
              <Sparkles className="w-16 h-16 text-text-muted mx-auto mb-4" />
              <h3 className="text-xl font-heading font-bold mb-2">No characters yet</h3>
              <p className="text-text-secondary mb-6">Create your own AI companion!</p>
              <Button
                onClick={() => navigate('/create-character')}
                className="bg-primary hover:bg-primary/90"
              >
                Create Character
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
              {characters.map((character, index) => (
                <motion.div
                  key={character.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="relative overflow-hidden rounded-2xl cursor-pointer group shadow-card hover:shadow-card-hover transition-all duration-300"
                >
                  <div className="aspect-[3/4] relative bg-background-paper">
                    <motion.img
                      src={character.avatar_url}
                      alt={character.name}
                      className="w-full h-full object-cover"
                      whileHover={{ scale: 1.1 }}
                      transition={{ duration: 0.3 }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                    
                    {/* Action Buttons */}
                    <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/chat/${character.id}`);
                        }}
                        className="p-2 rounded-full glass-heavy hover:bg-primary/20"
                      >
                        <MessageCircle className="w-4 h-4 text-primary" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(character.id);
                        }}
                        className="p-2 rounded-full glass-heavy hover:bg-red-500/20"
                      >
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </button>
                    </div>

                    <div className="absolute top-3 left-3">
                      <div className="px-2 py-1 rounded-full glass-heavy text-xs font-medium">
                        Custom
                      </div>
                    </div>
                  </div>

                  <div 
                    className="absolute bottom-0 left-0 right-0 p-4"
                    onClick={() => navigate(`/chat/${character.id}`)}
                  >
                    <h3 className="text-lg font-heading font-bold text-white mb-1">{character.name}</h3>
                    <p className="text-xs text-text-secondary mb-2">{character.age} • {character.occupation || 'Custom AI'}</p>
                    <p className="text-xs text-text-secondary line-clamp-2">{character.description}</p>
                    
                    <div className="flex flex-wrap gap-1 mt-2">
                      {character.traits.slice(0, 2).map((trait) => (
                        <span
                          key={trait}
                          className="px-2 py-0.5 rounded-lg bg-primary/10 border border-primary/20 text-xs font-medium text-primary"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
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
