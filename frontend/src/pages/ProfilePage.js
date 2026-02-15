import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, User, Mail, Calendar, Edit2, Camera, Save, X, Crown, MessageCircle, Heart, Image as ImageIcon, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProfilePage({ user, onUpdateUser }) {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    totalChats: 0,
    favoriteCharacters: 0,
    customCharacters: 0,
    imagesGenerated: 0
  });
  const [formData, setFormData] = useState({
    username: user?.username || user?.name || "",
    email: user?.email || ""
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      // Fetch favorites count
      const favResponse = await axios.get(`${API}/favorites/${user.id}`);
      const favorites = favResponse.data.favorites || [];

      // Fetch custom characters count
      const charResponse = await axios.get(`${API}/characters/my/${user.id}`);
      const customChars = charResponse.data.characters || [];

      // Fetch chat count
      const chatResponse = await axios.get(`${API}/chat/my-chats?user_id=${user.id}`);
      const chats = chatResponse.data.chats || [];

      // Fetch images count
      const imgResponse = await axios.get(`${API}/images/my/${user.id}`);
      const images = imgResponse.data.images || [];

      setStats({
        totalChats: chats.length,
        favoriteCharacters: favorites.length,
        customCharacters: customChars.length,
        imagesGenerated: images.length
      });
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Update user profile (mock for now - would need backend endpoint)
      const updatedUser = { ...user, username: formData.username };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      if (onUpdateUser) {
        onUpdateUser(updatedUser);
      }
      toast.success("Profile updated successfully!");
      setIsEditing(false);
    } catch (error) {
      toast.error("Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const memberSince = user?.created_at 
    ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : "Recently joined";

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Button
                data-testid="back-btn"
                onClick={() => navigate('/characters')}
                variant="ghost"
                className="text-text-secondary hover:text-white"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Back
              </Button>
              <h1 className="text-xl font-heading font-bold">Profile</h1>
            </div>
            {!isEditing ? (
              <Button
                data-testid="edit-profile-btn"
                onClick={() => setIsEditing(true)}
                variant="ghost"
                className="text-primary hover:text-primary/80"
              >
                <Edit2 className="w-4 h-4 mr-2" />
                Edit Profile
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button
                  data-testid="cancel-edit-btn"
                  onClick={() => {
                    setIsEditing(false);
                    setFormData({
                      username: user?.username || user?.name || "",
                      email: user?.email || ""
                    });
                  }}
                  variant="ghost"
                  className="text-text-secondary"
                >
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
                <Button
                  data-testid="save-profile-btn"
                  onClick={handleSave}
                  disabled={loading}
                  className="bg-primary hover:bg-primary/90"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save
                </Button>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Profile Header Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-heavy rounded-3xl p-8 mb-8"
          >
            <div className="flex flex-col md:flex-row items-center gap-8">
              {/* Avatar */}
              <div className="relative group">
                <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary to-accent-purple p-1">
                  <div className="w-full h-full rounded-full bg-background flex items-center justify-center overflow-hidden">
                    {user?.picture ? (
                      <img 
                        src={user.picture} 
                        alt="Profile" 
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <User className="w-16 h-16 text-primary" />
                    )}
                  </div>
                </div>
                <button 
                  className="absolute bottom-2 right-2 w-10 h-10 rounded-full bg-primary flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => toast.info("Avatar upload coming soon!")}
                >
                  <Camera className="w-5 h-5 text-white" />
                </button>
              </div>

              {/* Info */}
              <div className="flex-1 text-center md:text-left">
                {isEditing ? (
                  <div className="space-y-4 max-w-md">
                    <div>
                      <label className="text-sm text-text-secondary mb-1 block">Username</label>
                      <Input
                        data-testid="username-input"
                        value={formData.username}
                        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                        className="bg-white/5 border-white/10 focus:border-primary"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-text-secondary mb-1 block">Email</label>
                      <Input
                        data-testid="email-input"
                        value={formData.email}
                        disabled
                        className="bg-white/5 border-white/10 opacity-50 cursor-not-allowed"
                      />
                      <p className="text-xs text-text-muted mt-1">Email cannot be changed</p>
                    </div>
                  </div>
                ) : (
                  <>
                    <h2 className="text-3xl font-heading font-bold mb-2">
                      {user?.username || user?.name || "User"}
                    </h2>
                    <div className="flex flex-col md:flex-row items-center gap-4 text-text-secondary">
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4" />
                        <span>{user?.email}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>Member since {memberSince}</span>
                      </div>
                    </div>
                  </>
                )}

                {/* Subscription Badge */}
                <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-gray-500/20 to-gray-600/20 border border-gray-500/30">
                  <Crown className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-400">Free Plan</span>
                  <Button
                    onClick={() => navigate('/subscription')}
                    size="sm"
                    className="ml-2 bg-gradient-to-r from-primary to-accent-purple text-xs h-7"
                  >
                    Upgrade
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Stats Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
          >
            <div className="glass rounded-2xl p-6 text-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mx-auto mb-3">
                <MessageCircle className="w-6 h-6 text-white" />
              </div>
              <p className="text-3xl font-bold text-white mb-1">{stats.totalChats}</p>
              <p className="text-sm text-text-secondary">Conversations</p>
            </div>

            <div className="glass rounded-2xl p-6 text-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center mx-auto mb-3">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <p className="text-3xl font-bold text-white mb-1">{stats.favoriteCharacters}</p>
              <p className="text-sm text-text-secondary">Favorites</p>
            </div>

            <div className="glass rounded-2xl p-6 text-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <p className="text-3xl font-bold text-white mb-1">{stats.customCharacters}</p>
              <p className="text-sm text-text-secondary">Custom AI</p>
            </div>

            <div className="glass rounded-2xl p-6 text-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-3">
                <ImageIcon className="w-6 h-6 text-white" />
              </div>
              <p className="text-3xl font-bold text-white mb-1">{stats.imagesGenerated}</p>
              <p className="text-sm text-text-secondary">Images Created</p>
            </div>
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-heavy rounded-2xl p-6"
          >
            <h3 className="text-lg font-heading font-bold mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button
                data-testid="action-collection"
                onClick={() => navigate('/collection')}
                variant="ghost"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-white/5"
              >
                <Heart className="w-6 h-6 text-primary" />
                <span className="text-sm">My Collection</span>
              </Button>

              <Button
                data-testid="action-my-ai"
                onClick={() => navigate('/my-ai')}
                variant="ghost"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-white/5"
              >
                <Sparkles className="w-6 h-6 text-amber-400" />
                <span className="text-sm">My AI</span>
              </Button>

              <Button
                data-testid="action-create"
                onClick={() => navigate('/create-character')}
                variant="ghost"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-white/5"
              >
                <User className="w-6 h-6 text-green-400" />
                <span className="text-sm">Create Character</span>
              </Button>

              <Button
                data-testid="action-generate"
                onClick={() => navigate('/generate-image')}
                variant="ghost"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-white/5"
              >
                <ImageIcon className="w-6 h-6 text-blue-400" />
                <span className="text-sm">Generate Image</span>
              </Button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
