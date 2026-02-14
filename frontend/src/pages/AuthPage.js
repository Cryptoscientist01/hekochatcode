import { useState } from "react";
import { motion } from "framer-motion";
import { Heart } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AuthPage({ onAuth }) {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/signup';
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : formData;
      
      const response = await axios.post(`${API}${endpoint}`, payload);
      
      toast.success(isLogin ? "Welcome back!" : "Account created successfully!");
      onAuth(response.data.token, response.data.user);
      navigate('/characters');
    } catch (error) {
      toast.error(error.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 bg-gradient-to-b from-primary/10 via-background to-background">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="glass-heavy rounded-2xl p-8">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2 mb-8">
            <Heart className="w-10 h-10 text-primary" fill="#FF0080" />
            <span className="text-3xl font-heading font-bold">Electric Candy</span>
          </div>

          <h2 className="text-2xl font-heading font-bold text-center mb-6">
            {isLogin ? "Welcome Back" : "Create Account"}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Input
                data-testid="email-input"
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="bg-white/5 border-white/10 focus:border-primary focus:ring-1 focus:ring-primary rounded-xl p-4 text-white placeholder:text-white/30"
                required
              />
            </div>

            {!isLogin && (
              <div>
                <Input
                  data-testid="username-input"
                  type="text"
                  placeholder="Username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="bg-white/5 border-white/10 focus:border-primary focus:ring-1 focus:ring-primary rounded-xl p-4 text-white placeholder:text-white/30"
                  required
                />
              </div>
            )}

            <div>
              <Input
                data-testid="password-input"
                type="password"
                placeholder="Password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="bg-white/5 border-white/10 focus:border-primary focus:ring-1 focus:ring-primary rounded-xl p-4 text-white placeholder:text-white/30"
                required
              />
            </div>

            <Button
              data-testid="submit-btn"
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary/90 text-white rounded-full py-6 font-bold shadow-neon"
            >
              {loading ? "Loading..." : (isLogin ? "Sign In" : "Create Account")}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              data-testid="toggle-auth-btn"
              onClick={() => setIsLogin(!isLogin)}
              className="text-text-secondary hover:text-primary transition-colors"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}