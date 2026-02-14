import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Heart, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CharactersPage({ user, onLogout }) {
  const navigate = useNavigate();
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCharacters();
  }, []);

  const fetchCharacters = async () => {
    try {
      const response = await axios.get(`${API}/characters`);
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

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-heavy">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button
              data-testid="back-btn"
              onClick={() => navigate('/')}
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10"
            >
              <ArrowLeft className="w-6 h-6" />
            </Button>
            <div className="flex items-center gap-2">
              <Heart className="w-8 h-8 text-primary" fill="#FF0080" />
              <span className="text-2xl font-heading font-bold">Electric Candy</span>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-text-secondary">Hi, {user.username}!</span>
            <Button
              data-testid="logout-btn"
              onClick={onLogout}
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10 rounded-full px-6"
            >
              Logout
            </Button>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 px-6 pb-12">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-4xl md:text-6xl font-heading font-bold mb-4">
              Choose Your <span className="bg-gradient-to-r from-primary to-accent-purple bg-clip-text text-transparent">Companion</span>
            </h1>
            <p className="text-lg text-text-secondary">
              Select an AI girlfriend to start your journey
            </p>
          </motion.div>

          {loading ? (
            <div className="text-center text-text-secondary">Loading characters...</div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {characters.map((character, index) => (
                <motion.div
                  key={character.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => handleSelectCharacter(character.id)}
                  data-testid={`character-card-${character.id}`}
                  className="relative overflow-hidden rounded-2xl cursor-pointer group transition-transform hover:scale-105"
                >
                  {/* Character Image */}
                  <div className="aspect-[3/4] relative">
                    <img
                      src={character.avatar_url}
                      alt={character.name}
                      className="w-full h-full object-cover"
                    />
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                  </div>

                  {/* Character Info */}
                  <div className="absolute bottom-0 left-0 right-0 p-6">
                    <h3 className="text-2xl font-heading font-bold mb-2">{character.name}</h3>
                    <p className="text-text-secondary text-sm mb-3">{character.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {character.traits.map((trait) => (
                        <span
                          key={trait}
                          className="px-3 py-1 rounded-full bg-primary/20 border border-primary/30 text-xs font-semibold"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Hover Effect */}
                  <div className="absolute inset-0 border-2 border-primary opacity-0 group-hover:opacity-100 transition-opacity neon-glow rounded-2xl" />
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}