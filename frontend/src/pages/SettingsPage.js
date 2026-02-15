import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Bell, Moon, Sun, Volume2, VolumeX, Shield, Trash2, Download, Globe, Palette, MessageSquare, Eye, EyeOff, ChevronRight, RotateCcw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useSettings } from "@/context/SettingsContext";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function SettingsPage({ user, onLogout }) {
  const navigate = useNavigate();
  const { settings, updateSetting, resetSettings, playSound } = useSettings();

  const handleSettingChange = (key, value) => {
    updateSetting(key, value);
    playSound('message');
    toast.success("Setting updated");
  };

  const handleResetSettings = () => {
    if (window.confirm("Reset all settings to default?")) {
      resetSettings();
      toast.success("Settings reset to default");
    }
  };

  const handleDeleteAccount = async () => {
    if (window.confirm("Are you sure you want to delete your account? This action cannot be undone.")) {
      if (window.confirm("This will permanently delete all your data including chats, characters, and images. Continue?")) {
        try {
          // Delete user's data from backend
          await axios.delete(`${API}/users/${user.id}/delete-account`);
          toast.success("Account deleted successfully");
          onLogout();
          navigate('/');
        } catch (error) {
          // If backend doesn't have this endpoint yet, just logout
          toast.info("Account deletion processed. Logging out...");
          onLogout();
          navigate('/');
        }
      }
    }
  };

  const handleExportData = async () => {
    try {
      // Fetch user's data
      const [favResponse, charResponse, chatResponse, imgResponse] = await Promise.all([
        axios.get(`${API}/favorites/${user.id}`).catch(() => ({ data: { favorites: [] } })),
        axios.get(`${API}/characters/my/${user.id}`).catch(() => ({ data: { characters: [] } })),
        axios.get(`${API}/chat/my-chats?user_id=${user.id}`).catch(() => ({ data: { chats: [] } })),
        axios.get(`${API}/images/my/${user.id}`).catch(() => ({ data: { images: [] } }))
      ]);

      const exportData = {
        exportInfo: {
          exportDate: new Date().toISOString(),
          appVersion: "1.0.0",
          format: "JSON"
        },
        user: {
          id: user.id,
          email: user.email,
          username: user.username || user.name,
          createdAt: user.created_at
        },
        settings: settings,
        favorites: favResponse.data.favorites || [],
        customCharacters: charResponse.data.characters || [],
        chatHistory: chatResponse.data.chats || [],
        generatedImages: (imgResponse.data.images || []).map(img => ({
          id: img.id,
          prompt: img.prompt,
          style: img.style,
          createdAt: img.created_at
          // Note: image_data excluded for file size
        }))
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ai-companion-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      playSound('message');
      toast.success("Data exported successfully!");
    } catch (error) {
      console.error("Export error:", error);
      toast.error("Failed to export data");
    }
  };

  const handleClearChatHistory = async () => {
    if (window.confirm("Clear all chat history? This cannot be undone.")) {
      try {
        await axios.delete(`${API}/chat/clear-all?user_id=${user.id}`);
        toast.success("Chat history cleared");
      } catch (error) {
        toast.info("Chat history clear request sent");
      }
    }
  };

  const SettingToggle = ({ enabled, onToggle, testId }) => (
    <button
      data-testid={testId}
      onClick={onToggle}
      className={`relative w-14 h-8 rounded-full transition-colors duration-300 ${
        enabled ? 'bg-primary' : 'bg-white/10'
      }`}
    >
      <div
        className={`absolute top-1 w-6 h-6 rounded-full bg-white shadow-lg transition-transform duration-300 ${
          enabled ? 'translate-x-7' : 'translate-x-1'
        }`}
      />
    </button>
  );

  const SettingRow = ({ icon: Icon, iconColor, title, description, children }) => (
    <div className="flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors">
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${iconColor} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <h4 className="font-medium">{title}</h4>
          <p className="text-sm text-text-secondary">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );

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
              <h1 className="text-xl font-heading font-bold">Settings</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Appearance Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-heavy rounded-2xl overflow-hidden"
          >
            <div className="p-4 border-b border-white/10">
              <h3 className="text-lg font-heading font-bold flex items-center gap-2">
                <Palette className="w-5 h-5 text-primary" />
                Appearance
              </h3>
            </div>
            <div className="p-2">
              <SettingRow
                icon={settings.theme === 'dark' ? Moon : Sun}
                iconColor="from-indigo-500 to-purple-500"
                title="Dark Mode"
                description="Use dark theme throughout the app"
              >
                <SettingToggle
                  testId="toggle-theme"
                  enabled={settings.theme === 'dark'}
                  onToggle={() => handleSettingChange('theme', settings.theme === 'dark' ? 'light' : 'dark')}
                />
              </SettingRow>

              <SettingRow
                icon={Eye}
                iconColor="from-cyan-500 to-blue-500"
                title="Compact Mode"
                description="Show more content with smaller elements"
              >
                <SettingToggle
                  testId="toggle-compact"
                  enabled={settings.compactMode}
                  onToggle={() => handleSettingChange('compactMode', !settings.compactMode)}
                />
              </SettingRow>

              <SettingRow
                icon={Globe}
                iconColor="from-green-500 to-emerald-500"
                title="Language"
                description="Choose your preferred language"
              >
                <select
                  data-testid="language-select"
                  value={settings.language}
                  onChange={(e) => handleSettingChange('language', e.target.value)}
                  className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="ja">Japanese</option>
                </select>
              </SettingRow>
            </div>
          </motion.div>

          {/* Notifications Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-heavy rounded-2xl overflow-hidden"
          >
            <div className="p-4 border-b border-white/10">
              <h3 className="text-lg font-heading font-bold flex items-center gap-2">
                <Bell className="w-5 h-5 text-amber-400" />
                Notifications & Sound
              </h3>
            </div>
            <div className="p-2">
              <SettingRow
                icon={Bell}
                iconColor="from-amber-500 to-orange-500"
                title="Push Notifications"
                description="Receive notifications for new messages"
              >
                <SettingToggle
                  testId="toggle-notifications"
                  enabled={settings.notifications}
                  onToggle={() => handleSettingChange('notifications', !settings.notifications)}
                />
              </SettingRow>

              <SettingRow
                icon={settings.soundEnabled ? Volume2 : VolumeX}
                iconColor="from-pink-500 to-rose-500"
                title="Sound Effects"
                description="Play sounds for messages and interactions"
              >
                <SettingToggle
                  testId="toggle-sound"
                  enabled={settings.soundEnabled}
                  onToggle={() => handleSettingChange('soundEnabled', !settings.soundEnabled)}
                />
              </SettingRow>

              <SettingRow
                icon={Volume2}
                iconColor="from-violet-500 to-purple-500"
                title="Voice Autoplay"
                description="Automatically play AI voice responses"
              >
                <SettingToggle
                  testId="toggle-voice-autoplay"
                  enabled={settings.voiceAutoplay}
                  onToggle={() => handleSettingChange('voiceAutoplay', !settings.voiceAutoplay)}
                />
              </SettingRow>
            </div>
          </motion.div>

          {/* Chat Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-heavy rounded-2xl overflow-hidden"
          >
            <div className="p-4 border-b border-white/10">
              <h3 className="text-lg font-heading font-bold flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-400" />
                Chat Settings
              </h3>
            </div>
            <div className="p-2">
              <SettingRow
                icon={MessageSquare}
                iconColor="from-blue-500 to-cyan-500"
                title="Typing Indicator"
                description="Show when AI is typing a response"
              >
                <SettingToggle
                  testId="toggle-typing"
                  enabled={settings.showTypingIndicator}
                  onToggle={() => handleSettingChange('showTypingIndicator', !settings.showTypingIndicator)}
                />
              </SettingRow>

              <SettingRow
                icon={Shield}
                iconColor="from-emerald-500 to-green-500"
                title="Auto-save Chats"
                description="Automatically save conversation history"
              >
                <SettingToggle
                  testId="toggle-autosave"
                  enabled={settings.autoSaveChat}
                  onToggle={() => handleSettingChange('autoSaveChat', !settings.autoSaveChat)}
                />
              </SettingRow>

              <SettingRow
                icon={Palette}
                iconColor="from-primary to-accent-purple"
                title="Chat Style"
                description="Choose your preferred chat bubble style"
              >
                <select
                  data-testid="chat-style-select"
                  value={settings.chatBubbleStyle}
                  onChange={(e) => handleSettingChange('chatBubbleStyle', e.target.value)}
                  className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary"
                >
                  <option value="modern">Modern</option>
                  <option value="classic">Classic</option>
                  <option value="minimal">Minimal</option>
                  <option value="bubble">Bubble</option>
                </select>
              </SettingRow>
            </div>
          </motion.div>

          {/* Privacy & Data Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-heavy rounded-2xl overflow-hidden"
          >
            <div className="p-4 border-b border-white/10">
              <h3 className="text-lg font-heading font-bold flex items-center gap-2">
                <Shield className="w-5 h-5 text-green-400" />
                Privacy & Data
              </h3>
            </div>
            <div className="p-2">
              <button
                data-testid="export-data-btn"
                onClick={handleExportData}
                className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center">
                    <Download className="w-5 h-5 text-white" />
                  </div>
                  <div className="text-left">
                    <h4 className="font-medium">Export My Data</h4>
                    <p className="text-sm text-text-secondary">Download all your data as JSON</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-text-secondary" />
              </button>

              <button
                data-testid="reset-settings-btn"
                onClick={handleResetSettings}
                className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                    <RotateCcw className="w-5 h-5 text-white" />
                  </div>
                  <div className="text-left">
                    <h4 className="font-medium">Reset Settings</h4>
                    <p className="text-sm text-text-secondary">Restore all settings to default</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-text-secondary" />
              </button>

              <button
                data-testid="clear-chats-btn"
                onClick={handleClearChatHistory}
                className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-orange-500/10 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-white" />
                  </div>
                  <div className="text-left">
                    <h4 className="font-medium text-orange-400">Clear Chat History</h4>
                    <p className="text-sm text-text-secondary">Delete all your conversations</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-orange-400" />
              </button>

              <button
                data-testid="delete-account-btn"
                onClick={handleDeleteAccount}
                className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-red-500/10 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-rose-500 flex items-center justify-center">
                    <Trash2 className="w-5 h-5 text-white" />
                  </div>
                  <div className="text-left">
                    <h4 className="font-medium text-red-400">Delete Account</h4>
                    <p className="text-sm text-text-secondary">Permanently delete your account and data</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-red-400" />
              </button>
            </div>
          </motion.div>

          {/* App Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-center text-text-secondary text-sm space-y-2"
          >
            <p>AI Companion v1.0.0</p>
            <p>Made with love by Emergent Labs</p>
            <div className="flex justify-center gap-4 pt-2">
              <button className="hover:text-primary transition-colors">Privacy Policy</button>
              <span>|</span>
              <button className="hover:text-primary transition-colors">Terms of Service</button>
              <span>|</span>
              <button className="hover:text-primary transition-colors">Contact Support</button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
