import { useState } from "react";
import { motion } from "framer-motion";
import { Shield, Eye, EyeOff, Lock, Mail, AlertCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminLoginPage({ onAdminLogin }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(`${API}/admin/login`, {
        email,
        password
      });

      const { token, admin } = response.data;
      
      localStorage.setItem('admin_token', token);
      localStorage.setItem('admin', JSON.stringify(admin));
      
      if (onAdminLogin) {
        onAdminLogin(admin, token);
      }
      
      toast.success("Welcome back, Administrator!");
      navigate('/optimus/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid credentials");
      toast.error("Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-red-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Admin Badge */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-3 px-6 py-3 rounded-full glass-heavy border border-red-500/30">
            <Shield className="w-6 h-6 text-red-500" />
            <span className="text-lg font-heading font-bold text-red-500">ADMIN ACCESS</span>
          </div>
        </div>

        {/* Login Card */}
        <div className="glass-heavy rounded-3xl p-8 border border-white/10">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-heading font-bold mb-2">
              Admin <span className="text-red-500">Portal</span>
            </h1>
            <p className="text-text-secondary">
              Authorized personnel only
            </p>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-400 text-sm">{error}</span>
            </motion.div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  data-testid="admin-email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@admin.com"
                  required
                  className="pl-12 bg-white/5 border-white/10 focus:border-red-500 h-12"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  data-testid="admin-password-input"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="pl-12 pr-12 bg-white/5 border-white/10 focus:border-red-500 h-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-text-muted hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <Button
              data-testid="admin-login-btn"
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white font-bold"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating...
                </div>
              ) : (
                <>
                  <Shield className="w-5 h-5 mr-2" />
                  Access Admin Panel
                </>
              )}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-white/10 text-center">
            <p className="text-text-muted text-xs">
              This area is restricted to authorized administrators only.
              <br />
              All access attempts are logged.
            </p>
          </div>
        </div>

        {/* Back Link */}
        <div className="text-center mt-6">
          <button
            onClick={() => navigate('/')}
            className="text-text-secondary hover:text-white text-sm transition-colors"
          >
            ← Back to main site
          </button>
        </div>
      </motion.div>
    </div>
  );
}
