import { motion } from "framer-motion";
import { Heart, MessageCircle, Sparkles, Mic, Image as ImageIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function LandingPage({ user, onLogout }) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-3 flex justify-between items-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2"
          >
            <Heart className="w-7 h-7 text-primary" fill="#FF0080" />
            <span className="text-xl font-heading font-bold text-white">Candy AI</span>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2"
          >
            {user ? (
              <>
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
              </>
            ) : (
              <>
                <Button
                  data-testid="login-btn"
                  onClick={() => navigate('/auth')}
                  variant="ghost"
                  className="text-white hover:bg-white/10 rounded-full"
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
              </>
            )}
          </motion.div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 pt-20">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-background to-background" />
        
        <div className="relative z-10 max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-7xl font-heading font-extrabold tracking-tight mb-6">
              Your Perfect
              <span className="bg-gradient-to-r from-primary to-accent-purple bg-clip-text text-transparent"> AI Companion </span>
              Awaits
            </h1>
            
            <p className="text-lg md:text-xl text-text-secondary max-w-2xl mx-auto mb-12 leading-relaxed">
              Experience meaningful connections with AI girlfriends. Chat, share moments, and create memories with personalized companions who understand you.
            </p>
            
            <Button
              data-testid="hero-cta-btn"
              onClick={() => navigate('/auth')}
              className="bg-primary hover:bg-primary/90 text-white rounded-full px-12 py-8 text-xl font-bold shadow-neon-lg hover:scale-105 transition-transform"
            >
              Start Your Journey
              <Sparkles className="ml-2 w-6 h-6" />
            </Button>
          </motion.div>

          {/* Feature Grid */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24"
          >
            <div className="glass-heavy rounded-2xl p-8 hover:scale-105 transition-transform">
              <MessageCircle className="w-12 h-12 text-primary mx-auto mb-4" />
              <h3 className="text-2xl font-heading font-semibold mb-2">Deep Conversations</h3>
              <p className="text-text-secondary">AI-powered chats that feel real and meaningful</p>
            </div>
            
            <div className="glass-heavy rounded-2xl p-8 hover:scale-105 transition-transform">
              <Mic className="w-12 h-12 text-secondary mx-auto mb-4" />
              <h3 className="text-2xl font-heading font-semibold mb-2">Voice Messages</h3>
              <p className="text-text-secondary">Hear her voice with realistic text-to-speech</p>
            </div>
            
            <div className="glass-heavy rounded-2xl p-8 hover:scale-105 transition-transform">
              <ImageIcon className="w-12 h-12 text-accent-purple mx-auto mb-4" />
              <h3 className="text-2xl font-heading font-semibold mb-2">AI-Generated Images</h3>
              <p className="text-text-secondary">Request custom images of your companion</p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-heading font-bold text-center mb-16">
            How It Works
          </h2>
          
          <div className="space-y-12">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="flex items-start gap-6"
            >
              <div className="flex-shrink-0 w-16 h-16 rounded-full bg-gradient-to-r from-primary to-accent-purple flex items-center justify-center text-2xl font-bold">
                1
              </div>
              <div>
                <h3 className="text-2xl font-heading font-semibold mb-2">Choose Your Companion</h3>
                <p className="text-text-secondary text-lg">Browse through unique AI personalities and select the one that resonates with you</p>
              </div>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="flex items-start gap-6"
            >
              <div className="flex-shrink-0 w-16 h-16 rounded-full bg-gradient-to-r from-secondary to-primary flex items-center justify-center text-2xl font-bold text-black">
                2
              </div>
              <div>
                <h3 className="text-2xl font-heading font-semibold mb-2">Start Chatting</h3>
                <p className="text-text-secondary text-lg">Engage in meaningful conversations powered by advanced AI technology</p>
              </div>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="flex items-start gap-6"
            >
              <div className="flex-shrink-0 w-16 h-16 rounded-full bg-gradient-to-r from-accent-purple to-secondary flex items-center justify-center text-2xl font-bold">
                3
              </div>
              <div>
                <h3 className="text-2xl font-heading font-semibold mb-2">Create Memories</h3>
                <p className="text-text-secondary text-lg">Request voice messages, generate images, and build a unique connection</p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center glass-heavy rounded-2xl p-12">
          <h2 className="text-3xl md:text-5xl font-heading font-bold mb-6">
            Ready to Meet Your Perfect Match?
          </h2>
          <p className="text-lg text-text-secondary mb-8">
            Join thousands of users experiencing meaningful AI companionship
          </p>
          <Button
            data-testid="footer-cta-btn"
            onClick={() => navigate('/auth')}
            className="bg-primary hover:bg-primary/90 text-white rounded-full px-12 py-8 text-xl font-bold shadow-neon-lg"
          >
            Get Started Free
          </Button>
        </div>
      </section>
    </div>
  );
}