import { motion } from "framer-motion";
import { Heart, MessageCircle, Sparkles, ArrowRight, Zap, Image as ImageIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LandingPage({ user, onLogout }) {
  const navigate = useNavigate();
  const [featuredCharacters, setFeaturedCharacters] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("Girls");

  useEffect(() => {
    fetchFeaturedCharacters();
  }, [selectedCategory]);

  const fetchFeaturedCharacters = async () => {
    try {
      const response = await axios.get(`${API}/characters?category=${selectedCategory}`);
      setFeaturedCharacters(response.data);
    } catch (error) {
      console.error("Failed to fetch characters", error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
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
              <span className="text-xl font-heading font-bold text-white">AI Companion</span>
            </button>
            
            <div className="flex items-center gap-8">
              {!user && (
                <div className="hidden md:flex items-center gap-8">
                  <button
                    onClick={() => navigate('/characters/Girls')}
                    className="text-text-secondary hover:text-white transition-colors font-medium"
                  >
                    Girls
                  </button>
                  <button
                    onClick={() => navigate('/characters/Anime')}
                    className="text-text-secondary hover:text-white transition-colors font-medium"
                  >
                    Anime
                  </button>
                  <button
                    onClick={() => navigate('/characters/Guys')}
                    className="text-text-secondary hover:text-white transition-colors font-medium"
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
                    className="bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary/80 text-white rounded-xl px-6 py-2.5 font-semibold shadow-lg"
                  >
                    Characters
                  </Button>
                  <Button
                    data-testid="logout-btn"
                    onClick={onLogout}
                    variant="ghost"
                    className="text-text-secondary hover:text-white hover:bg-white/5 rounded-xl"
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
                    className="text-white hover:bg-white/5 rounded-xl px-5"
                  >
                    Sign In
                  </Button>
                  <Button
                    data-testid="get-started-btn"
                    onClick={() => navigate('/auth')}
                    className="bg-gradient-to-r from-primary to-accent-purple hover:from-primary/90 hover:to-accent-purple/90 text-white rounded-xl px-6 py-2.5 font-bold shadow-neon"
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
      <section className="relative pt-32 pb-24 px-6 overflow-hidden">
        <div className="absolute inset-0 gradient-mesh opacity-60"></div>
        
        <div className="relative max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-light mb-8">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-text-secondary">Powered by Advanced AI Technology</span>
            </div>
            
            <h1 className="text-6xl md:text-7xl lg:text-8xl font-heading font-extrabold tracking-tight mb-6 leading-tight">
              Connect with Your
              <span className="block bg-gradient-to-r from-primary via-accent-purple to-secondary bg-clip-text text-transparent mt-2">
                Perfect AI Companion
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-text-secondary max-w-3xl mx-auto mb-12 leading-relaxed font-light">
              Experience meaningful conversations with AI personalities designed to understand, engage, and grow with you.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button
                data-testid="hero-cta-btn"
                onClick={() => navigate('/auth')}
                className="bg-gradient-to-r from-primary to-accent-purple hover:from-primary/90 hover:to-accent-purple/90 text-white rounded-xl px-10 py-7 text-lg font-bold shadow-neon-lg hover:shadow-neon hover:scale-105 transition-all"
              >
                Start Chatting Now
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button
                onClick={() => navigate('/characters')}
                variant="outline"
                className="border-white/10 text-white hover:bg-white/5 rounded-xl px-10 py-7 text-lg font-semibold"
              >
                Explore Characters
              </Button>
            </div>
            
            <div className="mt-16 flex items-center justify-center gap-12 text-text-secondary">
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-1">25+</div>
                <div className="text-sm">AI Characters</div>
              </div>
              <div className="w-px h-12 bg-white/10"></div>
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-1">24/7</div>
                <div className="text-sm">Always Available</div>
              </div>
              <div className="w-px h-12 bg-white/10"></div>
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-1">100%</div>
                <div className="text-sm">Private & Secure</div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Featured Characters */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-heading font-bold mb-4">
              Meet Your Next <span className="text-primary">Connection</span>
            </h2>
            <p className="text-text-secondary text-lg max-w-2xl mx-auto">
              Choose from diverse AI personalities, each with unique traits and conversation styles
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-6 mb-12"
          >
            {featuredCharacters.map((character, index) => (
              <motion.div
                key={character.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                onClick={() => user ? navigate(`/chat/${character.id}`) : navigate('/auth')}
                className="relative overflow-hidden rounded-2xl cursor-pointer group shadow-card hover:shadow-card-hover transition-all duration-300"
              >
                <div className="aspect-[3/4] relative">
                  <img
                    src={character.avatar_url}
                    alt={character.name}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
                  
                  <div className="absolute top-3 right-3">
                    <div className="px-3 py-1.5 rounded-full glass-heavy text-xs font-semibold">
                      {character.category}
                    </div>
                  </div>
                </div>
                
                <div className="absolute bottom-0 left-0 right-0 p-5">
                  <h3 className="text-lg font-heading font-bold text-white mb-1">{character.name}</h3>
                  <p className="text-xs text-text-secondary mb-2">{character.age} • {character.occupation || 'Available'}</p>
                  <p className="text-sm text-text-secondary line-clamp-2">
                    {character.description}
                  </p>
                </div>

                <div className="absolute inset-0 border-2 border-primary opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl pointer-events-none" 
                     style={{ boxShadow: '0 0 30px rgba(255, 0, 128, 0.4)' }} />
              </motion.div>
            ))}
          </motion.div>

          <div className="text-center">
            <Button
              data-testid="view-all-btn"
              onClick={() => navigate(user ? '/characters' : '/auth')}
              className="bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-xl px-8 py-6 text-base font-semibold"
            >
              View All 25+ Characters
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6 bg-gradient-to-b from-background via-background-paper to-background">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-heading font-bold mb-4">
              Everything You Need for <span className="text-primary">Meaningful Connections</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="glass-light rounded-2xl p-8 hover:bg-white/[0.07] transition-all duration-300 group"
            >
              <div className="w-14 h-14 mb-6 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                <MessageCircle className="w-7 h-7 text-primary" />
              </div>
              <h3 className="text-xl font-heading font-bold mb-3">Natural Conversations</h3>
              <p className="text-text-secondary leading-relaxed">Experience AI-powered chats that feel genuine and meaningful, powered by Gemini 3 Flash technology.</p>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="glass-light rounded-2xl p-8 hover:bg-white/[0.07] transition-all duration-300 group"
            >
              <div className="w-14 h-14 mb-6 rounded-xl bg-gradient-to-br from-secondary/20 to-secondary/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Zap className="w-7 h-7 text-secondary" />
              </div>
              <h3 className="text-xl font-heading font-bold mb-3">Voice Messages</h3>
              <p className="text-text-secondary leading-relaxed">Hear their voice with realistic text-to-speech powered by OpenAI's advanced TTS technology.</p>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
              className="glass-light rounded-2xl p-8 hover:bg-white/[0.07] transition-all duration-300 group"
            >
              <div className="w-14 h-14 mb-6 rounded-xl bg-gradient-to-br from-accent-purple/20 to-accent-purple/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                <ImageIcon className="w-7 h-7 text-accent-purple" />
              </div>
              <h3 className="text-xl font-heading font-bold mb-3">AI-Generated Images</h3>
              <p className="text-text-secondary leading-relaxed">Request custom images of your companion using Gemini Nano Banana image generation.</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-heading font-bold mb-4">
              Explore by <span className="text-primary">Category</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { name: "Girls", count: "10", gradient: "from-primary to-primary/60" },
              { name: "Anime", count: "8", gradient: "from-secondary to-secondary/60" },
              { name: "Guys", count: "7", gradient: "from-accent-purple to-accent-purple/60" }
            ].map((category, index) => (
              <motion.button
                key={category.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                onClick={() => navigate(user ? `/characters/${category.name}` : '/auth')}
                className="glass-light rounded-2xl p-10 hover:bg-white/[0.07] transition-all duration-300 group text-left"
              >
                <div className={`w-16 h-16 mb-6 rounded-xl bg-gradient-to-br ${category.gradient} opacity-20 group-hover:opacity-30 transition-opacity`}></div>
                <h3 className="text-3xl font-heading font-bold mb-2">{category.name}</h3>
                <p className="text-text-secondary mb-6">{category.count}+ unique characters</p>
                <div className="flex items-center gap-2 text-primary group-hover:gap-3 transition-all">
                  <span className="font-semibold">Explore</span>
                  <ArrowRight className="w-5 h-5" />
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="relative overflow-hidden rounded-3xl p-12 md:p-16 text-center"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-accent-purple/20 to-secondary/20"></div>
            <div className="absolute inset-0 glass-heavy"></div>
            
            <div className="relative">
              <h2 className="text-4xl md:text-5xl font-heading font-bold mb-6">
                Start Your Journey Today
              </h2>
              <p className="text-xl text-text-secondary mb-10 max-w-2xl mx-auto">
                Join thousands experiencing meaningful AI companionship. No credit card required.
              </p>
              <Button
                data-testid="footer-cta-btn"
                onClick={() => navigate('/auth')}
                className="bg-gradient-to-r from-primary to-accent-purple hover:from-primary/90 hover:to-accent-purple/90 text-white rounded-xl px-12 py-7 text-lg font-bold shadow-neon-lg hover:scale-105 transition-all"
              >
                Get Started Free
                <Sparkles className="ml-2 w-5 h-5" />
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center">
                <Heart className="w-6 h-6 text-white" fill="white" />
              </div>
              <span className="text-lg font-heading font-bold text-white">AI Companion</span>
            </div>
            
            <div className="text-text-secondary text-sm text-center md:text-left">
              <p>© 2026 AI Companion. All Rights Reserved.</p>
              <p className="mt-1">Experience meaningful connections with advanced AI technology.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}