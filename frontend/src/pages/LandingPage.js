import { motion } from "framer-motion";
import { Heart, MessageCircle, Sparkles, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LandingPage({ user, onLogout }) {
  const navigate = useNavigate();
  const [featuredCharacters, setFeaturedCharacters] = useState([]);

  useEffect(() => {
    fetchFeaturedCharacters();
  }, []);

  const fetchFeaturedCharacters = async () => {
    try {
      const response = await axios.get(`${API}/characters`);
      // Get 6 random featured characters
      const shuffled = response.data.sort(() => 0.5 - Math.random());
      setFeaturedCharacters(shuffled.slice(0, 6));
    } catch (error) {
      console.error("Failed to fetch characters", error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Fixed Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex justify-between items-center">
            <button 
              onClick={() => navigate('/')}
              className="flex items-center gap-2 hover:opacity-80 transition-opacity"
            >
              <Heart className="w-7 h-7 text-primary" fill="#FF0080" />
              <span className="text-xl font-heading font-bold text-white">Candy AI</span>
            </button>
            
            <div className="flex items-center gap-6">
              {!user && (
                <div className="hidden md:flex items-center gap-6 text-sm">
                  <button
                    onClick={() => navigate('/characters/Girls')}
                    className="text-text-secondary hover:text-white transition-colors"
                  >
                    Girls
                  </button>
                  <button
                    onClick={() => navigate('/characters/Anime')}
                    className="text-text-secondary hover:text-white transition-colors"
                  >
                    Anime
                  </button>
                  <button
                    onClick={() => navigate('/characters/Guys')}
                    className="text-text-secondary hover:text-white transition-colors"
                  >
                    Guys
                  </button>
                </div>
              )}
              
              {user ? (
                <div className="flex items-center gap-3">
                  <Button
                    data-testid="dashboard-btn"
                    onClick={() => navigate('/characters')}
                    className="bg-primary hover:bg-primary/90 text-white rounded-full px-6 py-2 font-semibold"
                  >
                    Characters
                  </Button>
                  <Button
                    data-testid="logout-btn"
                    onClick={onLogout}
                    variant="ghost"
                    className="text-text-secondary hover:text-white hover:bg-white/10 rounded-full"
                  >
                    Logout
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <Button
                    data-testid="login-btn"
                    onClick={() => navigate('/auth')}
                    variant="ghost"
                    className="text-white hover:bg-white/10 rounded-full px-6"
                  >
                    Login
                  </Button>
                  <Button
                    data-testid="get-started-btn"
                    onClick={() => navigate('/auth')}
                    className="bg-primary hover:bg-primary/90 text-white rounded-full px-6 py-2 font-bold shadow-neon"
                  >
                    Get Started
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-5xl md:text-7xl font-heading font-extrabold tracking-tight mb-6">
              Your Perfect
              <span className="bg-gradient-to-r from-primary to-accent-purple bg-clip-text text-transparent"> AI Companion </span>
              Awaits
            </h1>
            
            <p className="text-lg md:text-xl text-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
              Experience meaningful connections with AI companions. Chat, share moments, and create memories with personalized characters who understand you.
            </p>
            
            <Button
              data-testid="hero-cta-btn"
              onClick={() => navigate('/auth')}
              className="bg-primary hover:bg-primary/90 text-white rounded-full px-10 py-7 text-lg font-bold shadow-neon-lg hover:scale-105 transition-all"
            >
              Start Your Journey
              <Sparkles className="ml-2 w-5 h-5" />
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Featured Characters */}
      <section className="py-16 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-5xl font-heading font-bold mb-4">
              Meet Our <span className="text-primary">Characters</span>
            </h2>
            <p className="text-text-secondary text-lg">
              Choose from diverse personalities and start chatting instantly
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8"
          >
            {featuredCharacters.map((character, index) => (
              <motion.div
                key={character.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                onClick={() => user ? navigate(`/chat/${character.id}`) : navigate('/auth')}
                className="relative overflow-hidden rounded-xl cursor-pointer group"
              >
                <div className="aspect-[3/4] relative">
                  <img
                    src={character.avatar_url}
                    alt={character.name}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                </div>
                
                <div className="absolute bottom-0 left-0 right-0 p-3">
                  <h3 className="text-base font-heading font-bold text-white">{character.name}</h3>
                  <p className="text-xs text-text-secondary">{character.age} • {character.category}</p>
                </div>

                <div className="absolute inset-0 border-2 border-primary opacity-0 group-hover:opacity-100 transition-opacity rounded-xl" 
                     style={{ boxShadow: '0 0 20px rgba(255, 0, 128, 0.3)' }} />
              </motion.div>
            ))}
          </motion.div>

          <div className="text-center">
            <Button
              data-testid="view-all-btn"
              onClick={() => navigate(user ? '/characters' : '/auth')}
              variant="outline"
              className="border-primary/30 text-primary hover:bg-primary/10 rounded-full px-8 py-6 text-base font-semibold"
            >
              View All Characters
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-gradient-to-b from-background to-background-paper">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <div className="glass-heavy rounded-2xl p-8 text-center hover:scale-105 transition-transform">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                <MessageCircle className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-xl font-heading font-semibold mb-3">Deep Conversations</h3>
              <p className="text-text-secondary">AI-powered chats that feel real and meaningful with Gemini 3 Flash</p>
            </div>
            
            <div className="glass-heavy rounded-2xl p-8 text-center hover:scale-105 transition-transform">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-secondary/10 flex items-center justify-center">
                <svg className="w-8 h-8 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <h3 className="text-xl font-heading font-semibold mb-3">Voice Messages</h3>
              <p className="text-text-secondary">Hear their voice with realistic OpenAI text-to-speech</p>
            </div>
            
            <div className="glass-heavy rounded-2xl p-8 text-center hover:scale-105 transition-transform">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-accent-purple/10 flex items-center justify-center">
                <svg className="w-8 h-8 text-accent-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-heading font-semibold mb-3">AI-Generated Images</h3>
              <p className="text-text-secondary">Request custom images using Gemini Nano Banana</p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Categories Preview */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-5xl font-heading font-bold mb-4">
              Explore by <span className="text-primary">Category</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { name: "Girls", count: "10+", color: "primary", emoji: "👩" },
              { name: "Anime", count: "8+", color: "secondary", emoji: "🎌" },
              { name: "Guys", count: "7+", color: "accent-purple", emoji: "👨" }
            ].map((category) => (
              <motion.button
                key={category.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                onClick={() => navigate(user ? `/characters/${category.name}` : '/auth')}
                className="glass-heavy rounded-2xl p-8 hover:scale-105 transition-all group"
              >
                <div className="text-5xl mb-4">{category.emoji}</div>
                <h3 className="text-2xl font-heading font-bold mb-2">{category.name}</h3>
                <p className="text-text-secondary mb-4">{category.count} characters available</p>
                <div className="text-primary group-hover:translate-x-2 transition-transform inline-flex items-center gap-2">
                  Explore <ArrowRight className="w-4 h-4" />
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="glass-heavy rounded-2xl p-12 text-center"
          >
            <h2 className="text-3xl md:text-5xl font-heading font-bold mb-6">
              Ready to Meet Your Perfect Match?
            </h2>
            <p className="text-lg text-text-secondary mb-8 max-w-2xl mx-auto">
              Join thousands experiencing meaningful AI companionship. Start chatting in seconds.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                data-testid="footer-cta-btn"
                onClick={() => navigate('/auth')}
                className="bg-primary hover:bg-primary/90 text-white rounded-full px-10 py-7 text-lg font-bold shadow-neon-lg"
              >
                Get Started Free
              </Button>
              <Button
                onClick={() => navigate(user ? '/characters' : '/auth')}
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10 rounded-full px-10 py-7 text-lg font-semibold"
              >
                Browse Characters
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6">
        <div className="max-w-7xl mx-auto text-center text-text-secondary text-sm">
          <p>© 2026 Candy AI. All Rights Reserved.</p>
          <p className="mt-2">Experience meaningful connections with AI companions.</p>
        </div>
      </footer>
    </div>
  );
}
