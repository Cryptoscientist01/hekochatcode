import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Shield, Users, MessageCircle, Image as ImageIcon, Heart, Sparkles,
  Settings, LogOut, Trash2, Search, ChevronLeft, ChevronRight,
  BarChart3, TrendingUp, Calendar, User, Lock, Mail, Eye, Save, FileText
} from "lucide-react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDashboard({ admin, adminToken, onAdminLogout }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("analytics");
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [characters, setCharacters] = useState({ default_characters: [], custom_characters: [] });
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [userPage, setUserPage] = useState(0);
  const [totalUsers, setTotalUsers] = useState(0);
  
  // Settings state
  const [showSettings, setShowSettings] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [savingSettings, setSavingSettings] = useState(false);

  const authHeaders = {
    headers: { Authorization: `Bearer ${adminToken}` }
  };

  useEffect(() => {
    if (!adminToken) {
      navigate('/optimus');
      return;
    }
    fetchData();
  }, [adminToken, activeTab, userPage]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === "analytics") {
        const res = await axios.get(`${API}/admin/analytics`, authHeaders);
        setAnalytics(res.data);
      } else if (activeTab === "users") {
        const res = await axios.get(`${API}/admin/users?skip=${userPage * 20}&limit=20`, authHeaders);
        setUsers(res.data.users);
        setTotalUsers(res.data.total);
      } else if (activeTab === "characters") {
        const res = await axios.get(`${API}/admin/characters`, authHeaders);
        setCharacters(res.data);
      }
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error("Session expired");
        handleLogout();
      } else {
        toast.error("Failed to fetch data");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin');
    if (onAdminLogout) onAdminLogout();
    navigate('/optimus');
  };

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm(`Delete user "${username}" and all their data?`)) return;
    
    try {
      await axios.delete(`${API}/admin/users/${userId}`, authHeaders);
      toast.success("User deleted");
      fetchData();
    } catch (error) {
      toast.error("Failed to delete user");
    }
  };

  const handleDeleteCharacter = async (charId, name, isCustom) => {
    if (!window.confirm(`Delete character "${name}"?`)) return;
    
    try {
      await axios.delete(`${API}/admin/characters/${charId}?is_custom=${isCustom}`, authHeaders);
      toast.success("Character deleted");
      fetchData();
    } catch (error) {
      toast.error("Failed to delete character");
    }
  };

  const handleUpdateCredentials = async (e) => {
    e.preventDefault();
    if (!currentPassword) {
      toast.error("Current password is required");
      return;
    }
    
    setSavingSettings(true);
    try {
      await axios.put(`${API}/admin/update-credentials`, {
        current_password: currentPassword,
        new_email: newEmail || null,
        new_username: newUsername || null,
        new_password: newPassword || null
      }, authHeaders);
      
      toast.success("Credentials updated successfully");
      setShowSettings(false);
      setCurrentPassword("");
      setNewEmail("");
      setNewUsername("");
      setNewPassword("");
      
      // Update local storage if email/username changed
      if (newEmail || newUsername) {
        const updatedAdmin = { ...admin };
        if (newEmail) updatedAdmin.email = newEmail;
        if (newUsername) updatedAdmin.username = newUsername;
        localStorage.setItem('admin', JSON.stringify(updatedAdmin));
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update credentials");
    } finally {
      setSavingSettings(false);
    }
  };

  const filteredUsers = users.filter(u => 
    u.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const StatCard = ({ icon: Icon, label, value, color, trend }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <div className="flex items-center gap-1 text-green-400 text-sm">
            <TrendingUp className="w-4 h-4" />
            {trend}
          </div>
        )}
      </div>
      <p className="text-3xl font-bold mb-1">{value.toLocaleString()}</p>
      <p className="text-text-secondary text-sm">{label}</p>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/30">
                <Shield className="w-5 h-5 text-red-500" />
                <span className="font-bold text-red-500">ADMIN</span>
              </div>
              <h1 className="text-xl font-heading font-bold hidden sm:block">Dashboard</h1>
            </div>
            
            <div className="flex items-center gap-3">
              <span className="text-text-secondary text-sm hidden sm:block">
                {admin?.username || admin?.email}
              </span>
              <Button
                data-testid="admin-settings-btn"
                onClick={() => setShowSettings(true)}
                variant="ghost"
                size="icon"
                className="text-text-secondary hover:text-white"
              >
                <Settings className="w-5 h-5" />
              </Button>
              <Button
                data-testid="admin-logout-btn"
                onClick={handleLogout}
                variant="ghost"
                className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
              >
                <LogOut className="w-5 h-5 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="fixed top-20 w-full z-40 glass border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1">
            {[
              { id: "analytics", label: "Analytics", icon: BarChart3 },
              { id: "users", label: "Users", icon: Users },
              { id: "characters", label: "Characters", icon: Sparkles },
              { id: "blog", label: "Blog", icon: FileText }
            ].map(tab => (
              <button
                key={tab.id}
                data-testid={`tab-${tab.id}`}
                onClick={() => tab.id === "blog" ? navigate("/optimus/blog") : setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium transition-all border-b-2 ${
                  activeTab === tab.id
                    ? "border-red-500 text-red-500"
                    : "border-transparent text-text-secondary hover:text-white"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="pt-36 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin" />
            </div>
          ) : (
            <>
              {/* Analytics Tab */}
              {activeTab === "analytics" && analytics && (
                <div className="space-y-8">
                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    <StatCard
                      icon={Users}
                      label="Total Users"
                      value={analytics.total_users}
                      color="from-blue-500 to-cyan-500"
                      trend={analytics.recent_users > 0 ? `+${analytics.recent_users} this week` : null}
                    />
                    <StatCard
                      icon={Sparkles}
                      label="Characters"
                      value={analytics.total_characters}
                      color="from-purple-500 to-pink-500"
                    />
                    <StatCard
                      icon={User}
                      label="Custom Characters"
                      value={analytics.total_custom_characters}
                      color="from-amber-500 to-orange-500"
                    />
                    <StatCard
                      icon={MessageCircle}
                      label="Messages"
                      value={analytics.total_messages}
                      color="from-green-500 to-emerald-500"
                    />
                    <StatCard
                      icon={ImageIcon}
                      label="Images Generated"
                      value={analytics.total_images}
                      color="from-red-500 to-rose-500"
                    />
                    <StatCard
                      icon={Heart}
                      label="Favorites"
                      value={analytics.total_favorites}
                      color="from-pink-500 to-rose-500"
                    />
                  </div>

                  {/* User Growth Chart */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-heavy rounded-2xl p-6"
                  >
                    <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-red-500" />
                      User Registrations (Last 7 Days)
                    </h3>
                    <div className="flex items-end gap-2 h-40">
                      {analytics.users_by_day?.map((day, i) => {
                        const maxCount = Math.max(...analytics.users_by_day.map(d => d.count), 1);
                        const height = (day.count / maxCount) * 100;
                        return (
                          <div key={i} className="flex-1 flex flex-col items-center gap-2">
                            <div 
                              className="w-full bg-gradient-to-t from-red-500 to-orange-500 rounded-t-lg transition-all"
                              style={{ height: `${Math.max(height, 5)}%` }}
                            />
                            <span className="text-xs text-text-muted">
                              {new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
                            </span>
                            <span className="text-xs font-bold">{day.count}</span>
                          </div>
                        );
                      })}
                    </div>
                  </motion.div>
                </div>
              )}

              {/* Users Tab */}
              {activeTab === "users" && (
                <div className="space-y-6">
                  {/* Search */}
                  <div className="flex items-center gap-4">
                    <div className="relative flex-1 max-w-md">
                      <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                      <Input
                        data-testid="user-search"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search users..."
                        className="pl-12 bg-white/5 border-white/10"
                      />
                    </div>
                    <span className="text-text-secondary text-sm">
                      {totalUsers} total users
                    </span>
                  </div>

                  {/* Users Table */}
                  <div className="glass-heavy rounded-2xl overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-white/5">
                        <tr>
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">User</th>
                          <th className="text-left p-4 text-sm font-medium text-text-secondary hidden md:table-cell">Joined</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary">Chats</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary hidden sm:table-cell">Favorites</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary hidden sm:table-cell">Custom AI</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredUsers.map((user, i) => (
                          <tr key={user.id} className="border-t border-white/5 hover:bg-white/5">
                            <td className="p-4">
                              <div>
                                <p className="font-medium">{user.username || "No username"}</p>
                                <p className="text-sm text-text-secondary">{user.email}</p>
                              </div>
                            </td>
                            <td className="p-4 text-text-secondary text-sm hidden md:table-cell">
                              {user.created_at ? new Date(user.created_at).toLocaleDateString() : "N/A"}
                            </td>
                            <td className="p-4 text-center">{user.chat_count || 0}</td>
                            <td className="p-4 text-center hidden sm:table-cell">{user.favorites_count || 0}</td>
                            <td className="p-4 text-center hidden sm:table-cell">{user.custom_chars_count || 0}</td>
                            <td className="p-4 text-right">
                              <Button
                                data-testid={`delete-user-${user.id}`}
                                onClick={() => handleDeleteUser(user.id, user.username || user.email)}
                                variant="ghost"
                                size="sm"
                                className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  <div className="flex items-center justify-between">
                    <Button
                      onClick={() => setUserPage(p => Math.max(0, p - 1))}
                      disabled={userPage === 0}
                      variant="ghost"
                    >
                      <ChevronLeft className="w-5 h-5 mr-2" />
                      Previous
                    </Button>
                    <span className="text-text-secondary">
                      Page {userPage + 1} of {Math.ceil(totalUsers / 20)}
                    </span>
                    <Button
                      onClick={() => setUserPage(p => p + 1)}
                      disabled={(userPage + 1) * 20 >= totalUsers}
                      variant="ghost"
                    >
                      Next
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                  </div>
                </div>
              )}

              {/* Characters Tab */}
              {activeTab === "characters" && (
                <div className="space-y-8">
                  {/* Default Characters */}
                  <div>
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-purple-400" />
                      Default Characters ({characters.total_default})
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                      {characters.default_characters?.map(char => (
                        <div key={char.id} className="glass rounded-xl p-3 group relative">
                          <img
                            src={char.avatar_url}
                            alt={char.name}
                            className="w-full aspect-square object-cover rounded-lg mb-2"
                          />
                          <p className="font-medium text-sm truncate">{char.name}</p>
                          <p className="text-xs text-text-secondary">{char.category}</p>
                          <button
                            onClick={() => handleDeleteCharacter(char.id, char.name, false)}
                            className="absolute top-2 right-2 p-2 rounded-lg bg-red-500/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Custom Characters */}
                  <div>
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                      <User className="w-5 h-5 text-amber-400" />
                      Custom Characters ({characters.total_custom})
                    </h3>
                    {characters.custom_characters?.length > 0 ? (
                      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                        {characters.custom_characters.map(char => (
                          <div key={char.id} className="glass rounded-xl p-3 group relative">
                            <img
                              src={char.avatar_url}
                              alt={char.name}
                              className="w-full aspect-square object-cover rounded-lg mb-2"
                            />
                            <p className="font-medium text-sm truncate">{char.name}</p>
                            <p className="text-xs text-text-secondary">Custom</p>
                            <button
                              onClick={() => handleDeleteCharacter(char.id, char.name, true)}
                              className="absolute top-2 right-2 p-2 rounded-lg bg-red-500/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-text-secondary">No custom characters yet</p>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/50 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md glass-heavy rounded-2xl p-6"
          >
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <Settings className="w-5 h-5 text-red-500" />
              Update Admin Credentials
            </h2>

            <form onSubmit={handleUpdateCredentials} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Current Password *</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                    required
                    className="pl-10 bg-white/5 border-white/10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">New Email (optional)</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="New email address"
                    className="pl-10 bg-white/5 border-white/10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">New Username (optional)</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    type="text"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="New username"
                    className="pl-10 bg-white/5 border-white/10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">New Password (optional)</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="New password"
                    className="pl-10 bg-white/5 border-white/10"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  onClick={() => setShowSettings(false)}
                  variant="ghost"
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={savingSettings}
                  className="flex-1 bg-gradient-to-r from-red-500 to-orange-500"
                >
                  {savingSettings ? "Saving..." : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Changes
                    </>
                  )}
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
