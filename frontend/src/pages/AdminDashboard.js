import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Shield, Users, MessageCircle, Image as ImageIcon, Heart, Sparkles,
  Settings, LogOut, Trash2, Search, ChevronLeft, ChevronRight,
  BarChart3, TrendingUp, Calendar, User, Lock, Mail, Eye, Save, FileText,
  Bell, Flag, DollarSign, Activity, UserPlus, Edit, AlertTriangle, 
  CheckCircle, Info, X, Send, Clock, Megaphone
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
  const [chatAnalytics, setChatAnalytics] = useState(null);
  const [revenueAnalytics, setRevenueAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [characters, setCharacters] = useState({ default_characters: [], custom_characters: [] });
  const [chats, setChats] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [activityLogs, setActivityLogs] = useState([]);
  const [activitySummary, setActivitySummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [userPage, setUserPage] = useState(0);
  const [totalUsers, setTotalUsers] = useState(0);
  
  // Modal states
  const [showSettings, setShowSettings] = useState(false);
  const [showAnnouncementModal, setShowAnnouncementModal] = useState(false);
  const [showNotificationModal, setShowNotificationModal] = useState(false);
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);
  const [showCharacterEditModal, setShowCharacterEditModal] = useState(false);
  
  // Form states
  const [currentPassword, setCurrentPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [savingSettings, setSavingSettings] = useState(false);
  
  // Announcement form
  const [announcementForm, setAnnouncementForm] = useState({
    title: "", message: "", type: "info", is_active: true, start_date: "", end_date: ""
  });
  const [editingAnnouncement, setEditingAnnouncement] = useState(null);
  
  // Notification form
  const [notificationForm, setNotificationForm] = useState({
    user_id: "", title: "", message: "", type: "info"
  });
  
  // Admin form
  const [adminForm, setAdminForm] = useState({
    email: "", username: "", password: "", role: "moderator"
  });
  
  // Chat modal state
  const [selectedChat, setSelectedChat] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  
  // Character edit state
  const [editingCharacter, setEditingCharacter] = useState(null);
  const [characterForm, setCharacterForm] = useState({
    name: "", age: "", personality: "", description: "", occupation: ""
  });

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
      switch (activeTab) {
        case "analytics":
          const [analyticsRes, chatAnalyticsRes] = await Promise.all([
            axios.get(`${API}/admin/analytics`, authHeaders),
            axios.get(`${API}/admin/analytics/chats`, authHeaders)
          ]);
          setAnalytics(analyticsRes.data);
          setChatAnalytics(chatAnalyticsRes.data);
          break;
        case "users":
          const usersRes = await axios.get(`${API}/admin/users?skip=${userPage * 20}&limit=20`, authHeaders);
          setUsers(usersRes.data.users);
          setTotalUsers(usersRes.data.total);
          break;
        case "characters":
          const charsRes = await axios.get(`${API}/admin/characters`, authHeaders);
          setCharacters(charsRes.data);
          break;
        case "moderation":
          const chatsRes = await axios.get(`${API}/admin/chats?limit=50`, authHeaders);
          setChats(chatsRes.data.chats);
          break;
        case "announcements":
          const announcementsRes = await axios.get(`${API}/admin/announcements`, authHeaders);
          setAnnouncements(announcementsRes.data.announcements);
          break;
        case "notifications":
          const notificationsRes = await axios.get(`${API}/admin/notifications`, authHeaders);
          setNotifications(notificationsRes.data.notifications);
          break;
        case "revenue":
          const revenueRes = await axios.get(`${API}/admin/analytics/revenue`, authHeaders);
          setRevenueAnalytics(revenueRes.data);
          break;
        case "admins":
          const adminsRes = await axios.get(`${API}/admin/admins`, authHeaders);
          setAdmins(adminsRes.data.admins);
          break;
        case "logs":
          const [logsRes, summaryRes] = await Promise.all([
            axios.get(`${API}/admin/activity-logs?limit=100`, authHeaders),
            axios.get(`${API}/admin/activity-logs/summary`, authHeaders)
          ]);
          setActivityLogs(logsRes.data.logs);
          setActivitySummary(summaryRes.data);
          break;
      }
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error("Session expired");
        handleLogout();
      } else if (error.response?.status === 403) {
        toast.error("Access denied - Super admin required");
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
      
      toast.success("Credentials updated");
      setShowSettings(false);
      setCurrentPassword("");
      setNewEmail("");
      setNewUsername("");
      setNewPassword("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update");
    } finally {
      setSavingSettings(false);
    }
  };

  // Announcement handlers
  const handleSaveAnnouncement = async () => {
    try {
      if (editingAnnouncement) {
        await axios.put(`${API}/admin/announcements/${editingAnnouncement}`, announcementForm, authHeaders);
        toast.success("Announcement updated");
      } else {
        await axios.post(`${API}/admin/announcements`, announcementForm, authHeaders);
        toast.success("Announcement created");
      }
      setShowAnnouncementModal(false);
      setEditingAnnouncement(null);
      setAnnouncementForm({ title: "", message: "", type: "info", is_active: true, start_date: "", end_date: "" });
      fetchData();
    } catch (error) {
      toast.error("Failed to save announcement");
    }
  };

  const handleDeleteAnnouncement = async (id) => {
    if (!window.confirm("Delete this announcement?")) return;
    try {
      await axios.delete(`${API}/admin/announcements/${id}`, authHeaders);
      toast.success("Announcement deleted");
      fetchData();
    } catch (error) {
      toast.error("Failed to delete");
    }
  };

  // Notification handlers
  const handleSendNotification = async () => {
    try {
      await axios.post(`${API}/admin/notifications`, {
        ...notificationForm,
        user_id: notificationForm.user_id || null
      }, authHeaders);
      toast.success("Notification sent");
      setShowNotificationModal(false);
      setNotificationForm({ user_id: "", title: "", message: "", type: "info" });
      fetchData();
    } catch (error) {
      toast.error("Failed to send notification");
    }
  };

  // Admin handlers
  const handleCreateAdmin = async () => {
    try {
      await axios.post(`${API}/admin/admins`, adminForm, authHeaders);
      toast.success("Admin created");
      setShowAdminModal(false);
      setAdminForm({ email: "", username: "", password: "", role: "moderator" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create admin");
    }
  };

  const handleDeleteAdmin = async (id, email) => {
    if (!window.confirm(`Delete admin "${email}"?`)) return;
    try {
      await axios.delete(`${API}/admin/admins/${id}`, authHeaders);
      toast.success("Admin deleted");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete");
    }
  };

  // Chat moderation handlers
  const handleViewChat = async (chatId) => {
    try {
      const res = await axios.get(`${API}/admin/chats/${chatId}/messages`, authHeaders);
      setChatMessages(res.data.messages);
      setSelectedChat(chatId);
      setShowChatModal(true);
    } catch (error) {
      toast.error("Failed to load chat");
    }
  };

  const handleDeleteChat = async (chatId) => {
    if (!window.confirm("Delete this entire conversation?")) return;
    try {
      await axios.delete(`${API}/admin/chats/${chatId}`, authHeaders);
      toast.success("Chat deleted");
      setShowChatModal(false);
      fetchData();
    } catch (error) {
      toast.error("Failed to delete chat");
    }
  };

  // Character edit handlers
  const handleEditCharacter = (char, isCustom) => {
    setEditingCharacter({ ...char, isCustom });
    setCharacterForm({
      name: char.name,
      age: char.age?.toString() || "",
      personality: char.personality || "",
      description: char.description || "",
      occupation: char.occupation || ""
    });
    setShowCharacterEditModal(true);
  };

  const handleSaveCharacter = async () => {
    try {
      await axios.put(
        `${API}/admin/characters/${editingCharacter.id}?is_custom=${editingCharacter.isCustom}`,
        {
          ...characterForm,
          age: parseInt(characterForm.age) || null
        },
        authHeaders
      );
      toast.success("Character updated");
      setShowCharacterEditModal(false);
      fetchData();
    } catch (error) {
      toast.error("Failed to update character");
    }
  };

  const filteredUsers = users.filter(u => 
    u.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const StatCard = ({ icon: Icon, label, value, color, trend, subtext }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        {trend && (
          <div className="flex items-center gap-1 text-green-400 text-xs">
            <TrendingUp className="w-3 h-3" />
            {trend}
          </div>
        )}
      </div>
      <p className="text-2xl font-bold mb-1">{typeof value === 'number' ? value.toLocaleString() : value}</p>
      <p className="text-text-secondary text-sm">{label}</p>
      {subtext && <p className="text-text-muted text-xs mt-1">{subtext}</p>}
    </motion.div>
  );

  const tabs = [
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "users", label: "Users", icon: Users },
    { id: "characters", label: "Characters", icon: Sparkles },
    { id: "moderation", label: "Moderation", icon: Flag },
    { id: "announcements", label: "Announcements", icon: Megaphone },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "revenue", label: "Revenue", icon: DollarSign },
    { id: "admins", label: "Admins", icon: Shield },
    { id: "logs", label: "Activity", icon: Activity },
    { id: "blog", label: "Blog", icon: FileText }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/30">
                <Shield className="w-4 h-4 text-red-500" />
                <span className="font-bold text-red-500 text-sm">ADMIN</span>
              </div>
              <h1 className="text-lg font-heading font-bold hidden sm:block">Dashboard</h1>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-text-secondary text-sm hidden sm:block">
                {admin?.username || admin?.email}
              </span>
              <Button onClick={() => setShowSettings(true)} variant="ghost" size="icon" className="text-text-secondary hover:text-white">
                <Settings className="w-5 h-5" />
              </Button>
              <Button onClick={handleLogout} variant="ghost" className="text-red-400 hover:text-red-300 hover:bg-red-500/10">
                <LogOut className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Tabs - Scrollable */}
      <div className="fixed top-14 w-full z-40 glass border-b border-white/5 overflow-x-auto">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 min-w-max">
            {tabs.map(tab => (
              <button
                key={tab.id}
                data-testid={`tab-${tab.id}`}
                onClick={() => tab.id === "blog" ? navigate("/optimus/blog") : setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-3 text-xs font-medium transition-all border-b-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? "border-red-500 text-red-500"
                    : "border-transparent text-text-secondary hover:text-white"
                }`}
              >
                <tab.icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="pt-28 pb-12 px-4">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin" />
            </div>
          ) : (
            <>
              {/* Analytics Tab */}
              {activeTab === "analytics" && analytics && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                    <StatCard icon={Users} label="Total Users" value={analytics.total_users} color="from-blue-500 to-cyan-500" trend={analytics.recent_users > 0 ? `+${analytics.recent_users}` : null} />
                    <StatCard icon={Sparkles} label="Characters" value={analytics.total_characters} color="from-purple-500 to-pink-500" />
                    <StatCard icon={User} label="Custom AI" value={analytics.total_custom_characters} color="from-amber-500 to-orange-500" />
                    <StatCard icon={MessageCircle} label="Messages" value={analytics.total_messages} color="from-green-500 to-emerald-500" />
                    <StatCard icon={ImageIcon} label="Images" value={analytics.total_images} color="from-red-500 to-rose-500" />
                    <StatCard icon={Heart} label="Favorites" value={analytics.total_favorites} color="from-pink-500 to-rose-500" />
                  </div>

                  <div className="grid lg:grid-cols-2 gap-6">
                    {/* User Growth Chart */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-heavy rounded-2xl p-5">
                      <h3 className="text-base font-bold mb-4 flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-red-500" />
                        User Registrations (7 Days)
                      </h3>
                      <div className="flex items-end gap-2 h-32">
                        {analytics.users_by_day?.map((day, i) => {
                          const maxCount = Math.max(...analytics.users_by_day.map(d => d.count), 1);
                          const height = (day.count / maxCount) * 100;
                          return (
                            <div key={i} className="flex-1 flex flex-col items-center gap-1">
                              <div className="w-full bg-gradient-to-t from-red-500 to-orange-500 rounded-t-lg transition-all" style={{ height: `${Math.max(height, 5)}%` }} />
                              <span className="text-[10px] text-text-muted">{new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}</span>
                              <span className="text-xs font-bold">{day.count}</span>
                            </div>
                          );
                        })}
                      </div>
                    </motion.div>

                    {/* Popular Characters */}
                    {chatAnalytics && (
                      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-heavy rounded-2xl p-5">
                        <h3 className="text-base font-bold mb-4 flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-purple-500" />
                          Popular Characters
                        </h3>
                        <div className="space-y-2">
                          {chatAnalytics.most_popular_characters?.slice(0, 5).map((char, i) => (
                            <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-white/5">
                              <span className="text-lg font-bold text-text-muted w-6">{i + 1}</span>
                              {char.avatar_url && <img src={char.avatar_url} alt="" className="w-8 h-8 rounded-full object-cover" />}
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm truncate">{char.name}</p>
                              </div>
                              <span className="text-text-secondary text-sm">{char.chat_count} chats</span>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {/* Most Active Users */}
                  {chatAnalytics && (
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-heavy rounded-2xl p-5">
                      <h3 className="text-base font-bold mb-4 flex items-center gap-2">
                        <Users className="w-4 h-4 text-blue-500" />
                        Most Active Users
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        {chatAnalytics.most_active_users?.slice(0, 5).map((user, i) => (
                          <div key={i} className="p-3 rounded-xl bg-white/5 text-center">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center mx-auto mb-2">
                              <span className="text-white font-bold">{user.username?.[0]?.toUpperCase() || "?"}</span>
                            </div>
                            <p className="font-medium text-sm truncate">{user.username || "Unknown"}</p>
                            <p className="text-text-secondary text-xs">{user.message_count} msgs</p>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </div>
              )}

              {/* Users Tab */}
              {activeTab === "users" && (
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="relative flex-1 max-w-md">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <Input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search users..." className="pl-10 bg-white/5 border-white/10" />
                    </div>
                    <span className="text-text-secondary text-sm">{totalUsers} users</span>
                  </div>

                  <div className="glass-heavy rounded-2xl overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-white/5">
                        <tr>
                          <th className="text-left p-3 font-medium text-text-secondary">User</th>
                          <th className="text-left p-3 font-medium text-text-secondary hidden md:table-cell">Joined</th>
                          <th className="text-center p-3 font-medium text-text-secondary">Chats</th>
                          <th className="text-center p-3 font-medium text-text-secondary hidden sm:table-cell">Favs</th>
                          <th className="text-right p-3 font-medium text-text-secondary">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredUsers.map((user) => (
                          <tr key={user.id} className="border-t border-white/5 hover:bg-white/5">
                            <td className="p-3">
                              <p className="font-medium">{user.username || "No name"}</p>
                              <p className="text-xs text-text-secondary">{user.email}</p>
                            </td>
                            <td className="p-3 text-text-secondary hidden md:table-cell">
                              {user.created_at ? new Date(user.created_at).toLocaleDateString() : "N/A"}
                            </td>
                            <td className="p-3 text-center">{user.chat_count || 0}</td>
                            <td className="p-3 text-center hidden sm:table-cell">{user.favorites_count || 0}</td>
                            <td className="p-3 text-right">
                              <Button onClick={() => handleDeleteUser(user.id, user.username || user.email)} variant="ghost" size="sm" className="text-red-400 hover:text-red-300">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex items-center justify-between">
                    <Button onClick={() => setUserPage(p => Math.max(0, p - 1))} disabled={userPage === 0} variant="ghost" size="sm">
                      <ChevronLeft className="w-4 h-4 mr-1" /> Prev
                    </Button>
                    <span className="text-text-secondary text-sm">Page {userPage + 1}</span>
                    <Button onClick={() => setUserPage(p => p + 1)} disabled={(userPage + 1) * 20 >= totalUsers} variant="ghost" size="sm">
                      Next <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}

              {/* Characters Tab */}
              {activeTab === "characters" && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-base font-bold mb-3 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      Default Characters ({characters.total_default})
                    </h3>
                    <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-8 gap-3">
                      {characters.default_characters?.map(char => (
                        <div key={char.id} className="glass rounded-xl p-2 group relative">
                          <img src={char.avatar_url} alt={char.name} className="w-full aspect-square object-cover rounded-lg mb-2" />
                          <p className="font-medium text-xs truncate">{char.name}</p>
                          <p className="text-[10px] text-text-secondary">{char.category}</p>
                          <div className="absolute top-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => handleEditCharacter(char, false)} className="p-1.5 rounded-lg bg-blue-500/80 text-white">
                              <Edit className="w-3 h-3" />
                            </button>
                            <button onClick={() => handleDeleteCharacter(char.id, char.name, false)} className="p-1.5 rounded-lg bg-red-500/80 text-white">
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-base font-bold mb-3 flex items-center gap-2">
                      <User className="w-4 h-4 text-amber-400" />
                      Custom Characters ({characters.total_custom})
                    </h3>
                    {characters.custom_characters?.length > 0 ? (
                      <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-8 gap-3">
                        {characters.custom_characters.map(char => (
                          <div key={char.id} className="glass rounded-xl p-2 group relative">
                            <img src={char.avatar_url} alt={char.name} className="w-full aspect-square object-cover rounded-lg mb-2" />
                            <p className="font-medium text-xs truncate">{char.name}</p>
                            <div className="absolute top-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button onClick={() => handleEditCharacter(char, true)} className="p-1.5 rounded-lg bg-blue-500/80 text-white">
                                <Edit className="w-3 h-3" />
                              </button>
                              <button onClick={() => handleDeleteCharacter(char.id, char.name, true)} className="p-1.5 rounded-lg bg-red-500/80 text-white">
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-text-secondary">No custom characters</p>
                    )}
                  </div>
                </div>
              )}

              {/* Moderation Tab */}
              {activeTab === "moderation" && (
                <div className="space-y-4">
                  <h3 className="text-base font-bold flex items-center gap-2">
                    <Flag className="w-4 h-4 text-orange-500" />
                    Chat Conversations ({chats.length})
                  </h3>
                  <div className="glass-heavy rounded-2xl overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-white/5">
                        <tr>
                          <th className="text-left p-3 font-medium text-text-secondary">User</th>
                          <th className="text-left p-3 font-medium text-text-secondary">Character</th>
                          <th className="text-center p-3 font-medium text-text-secondary">Messages</th>
                          <th className="text-left p-3 font-medium text-text-secondary hidden md:table-cell">Last Message</th>
                          <th className="text-right p-3 font-medium text-text-secondary">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {chats.map((chat) => (
                          <tr key={chat.chat_id} className="border-t border-white/5 hover:bg-white/5">
                            <td className="p-3">
                              <p className="font-medium">{chat.user_name}</p>
                              <p className="text-xs text-text-secondary">{chat.user_email}</p>
                            </td>
                            <td className="p-3 text-text-secondary">{chat.character_name}</td>
                            <td className="p-3 text-center">{chat.message_count}</td>
                            <td className="p-3 text-text-secondary text-xs hidden md:table-cell max-w-xs truncate">{chat.last_message}</td>
                            <td className="p-3 text-right">
                              <div className="flex justify-end gap-1">
                                <Button onClick={() => handleViewChat(chat.chat_id)} variant="ghost" size="sm">
                                  <Eye className="w-4 h-4" />
                                </Button>
                                <Button onClick={() => handleDeleteChat(chat.chat_id)} variant="ghost" size="sm" className="text-red-400">
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Announcements Tab */}
              {activeTab === "announcements" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold flex items-center gap-2">
                      <Megaphone className="w-4 h-4 text-yellow-500" />
                      Announcements ({announcements.length})
                    </h3>
                    <Button onClick={() => { setEditingAnnouncement(null); setAnnouncementForm({ title: "", message: "", type: "info", is_active: true, start_date: "", end_date: "" }); setShowAnnouncementModal(true); }} className="bg-gradient-to-r from-yellow-500 to-orange-500">
                      <Bell className="w-4 h-4 mr-2" /> New Announcement
                    </Button>
                  </div>
                  
                  <div className="grid gap-4">
                    {announcements.map(ann => (
                      <div key={ann.id} className={`glass rounded-xl p-4 border-l-4 ${ann.type === 'warning' ? 'border-yellow-500' : ann.type === 'error' ? 'border-red-500' : ann.type === 'success' ? 'border-green-500' : 'border-blue-500'}`}>
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-bold">{ann.title}</h4>
                              <span className={`px-2 py-0.5 rounded-full text-xs ${ann.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                                {ann.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </div>
                            <p className="text-text-secondary text-sm">{ann.message}</p>
                            <p className="text-text-muted text-xs mt-2">By {ann.created_by} · {new Date(ann.created_at).toLocaleDateString()}</p>
                          </div>
                          <div className="flex gap-1">
                            <Button onClick={() => { setEditingAnnouncement(ann.id); setAnnouncementForm(ann); setShowAnnouncementModal(true); }} variant="ghost" size="sm">
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button onClick={() => handleDeleteAnnouncement(ann.id)} variant="ghost" size="sm" className="text-red-400">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                    {announcements.length === 0 && <p className="text-text-secondary text-center py-8">No announcements yet</p>}
                  </div>
                </div>
              )}

              {/* Notifications Tab */}
              {activeTab === "notifications" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold flex items-center gap-2">
                      <Bell className="w-4 h-4 text-blue-500" />
                      Sent Notifications ({notifications.length})
                    </h3>
                    <Button onClick={() => setShowNotificationModal(true)} className="bg-gradient-to-r from-blue-500 to-purple-500">
                      <Send className="w-4 h-4 mr-2" /> Send Notification
                    </Button>
                  </div>
                  
                  <div className="glass-heavy rounded-2xl overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-white/5">
                        <tr>
                          <th className="text-left p-3 font-medium text-text-secondary">Title</th>
                          <th className="text-left p-3 font-medium text-text-secondary">Message</th>
                          <th className="text-center p-3 font-medium text-text-secondary">To</th>
                          <th className="text-center p-3 font-medium text-text-secondary">Type</th>
                          <th className="text-right p-3 font-medium text-text-secondary">Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {notifications.map(notif => (
                          <tr key={notif.id} className="border-t border-white/5">
                            <td className="p-3 font-medium">{notif.title}</td>
                            <td className="p-3 text-text-secondary max-w-xs truncate">{notif.message}</td>
                            <td className="p-3 text-center">
                              <span className="px-2 py-1 rounded-full bg-white/10 text-xs">{notif.user_id || 'All Users'}</span>
                            </td>
                            <td className="p-3 text-center">
                              <span className={`px-2 py-1 rounded-full text-xs ${notif.type === 'warning' ? 'bg-yellow-500/20 text-yellow-400' : notif.type === 'error' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                {notif.type}
                              </span>
                            </td>
                            <td className="p-3 text-right text-text-secondary">{new Date(notif.created_at).toLocaleDateString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Revenue Tab */}
              {activeTab === "revenue" && revenueAnalytics && (
                <div className="space-y-6">
                  {revenueAnalytics.is_mocked && (
                    <div className="glass rounded-xl p-4 border border-yellow-500/30 bg-yellow-500/10">
                      <div className="flex items-center gap-2 text-yellow-400">
                        <AlertTriangle className="w-5 h-5" />
                        <span className="font-medium">Simulated Data</span>
                      </div>
                      <p className="text-sm text-text-secondary mt-1">{revenueAnalytics.note}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard icon={DollarSign} label="Monthly Revenue" value={`$${revenueAnalytics.monthly_revenue}`} color="from-green-500 to-emerald-500" />
                    <StatCard icon={TrendingUp} label="Annual Projected" value={`$${revenueAnalytics.annual_projected}`} color="from-blue-500 to-cyan-500" />
                    <StatCard icon={Users} label="Free Users" value={revenueAnalytics.subscription_breakdown.free} color="from-gray-500 to-gray-600" />
                    <StatCard icon={Sparkles} label="Premium Users" value={revenueAnalytics.subscription_breakdown.premium + revenueAnalytics.subscription_breakdown.ultimate} color="from-purple-500 to-pink-500" subtext={`${revenueAnalytics.subscription_breakdown.premium} Premium, ${revenueAnalytics.subscription_breakdown.ultimate} Ultimate`} />
                  </div>

                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-heavy rounded-2xl p-5">
                    <h3 className="text-base font-bold mb-4 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      Revenue Trend (6 Months)
                    </h3>
                    <div className="flex items-end gap-3 h-40">
                      {revenueAnalytics.revenue_trend?.map((month, i) => {
                        const maxRev = Math.max(...revenueAnalytics.revenue_trend.map(m => m.revenue), 1);
                        const height = (month.revenue / maxRev) * 100;
                        return (
                          <div key={i} className="flex-1 flex flex-col items-center gap-2">
                            <div className="w-full bg-gradient-to-t from-green-500 to-emerald-400 rounded-t-lg transition-all" style={{ height: `${Math.max(height, 5)}%` }} />
                            <span className="text-xs text-text-muted">{month.month}</span>
                            <span className="text-xs font-bold">${month.revenue}</span>
                          </div>
                        );
                      })}
                    </div>
                  </motion.div>
                </div>
              )}

              {/* Admins Tab */}
              {activeTab === "admins" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold flex items-center gap-2">
                      <Shield className="w-4 h-4 text-red-500" />
                      Admin Accounts ({admins.length})
                    </h3>
                    <Button onClick={() => setShowAdminModal(true)} className="bg-gradient-to-r from-red-500 to-orange-500">
                      <UserPlus className="w-4 h-4 mr-2" /> Add Admin
                    </Button>
                  </div>

                  <div className="grid gap-4">
                    {admins.map(adm => (
                      <div key={adm.id} className="glass rounded-xl p-4 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
                            <span className="text-white font-bold text-lg">{adm.username?.[0]?.toUpperCase() || "A"}</span>
                          </div>
                          <div>
                            <p className="font-bold">{adm.username}</p>
                            <p className="text-text-secondary text-sm">{adm.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${adm.is_super_admin ? 'bg-red-500/20 text-red-400' : adm.role === 'admin' ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}>
                            {adm.is_super_admin ? 'Super Admin' : adm.role || 'Admin'}
                          </span>
                          {adm.id !== admin?.id && (
                            <Button onClick={() => handleDeleteAdmin(adm.id, adm.email)} variant="ghost" size="sm" className="text-red-400">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Activity Logs Tab */}
              {activeTab === "logs" && (
                <div className="space-y-6">
                  {activitySummary && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                      <StatCard icon={Activity} label="Total Actions" value={activitySummary.total_logs} color="from-purple-500 to-pink-500" />
                      <StatCard icon={Clock} label="Last 24 Hours" value={activitySummary.recent_activity_count} color="from-blue-500 to-cyan-500" />
                      <StatCard icon={CheckCircle} label="Most Common" value={activitySummary.actions_by_type?.[0]?.action || "N/A"} color="from-green-500 to-emerald-500" />
                      <StatCard icon={User} label="Most Active" value={activitySummary.actions_by_admin?.[0]?.admin?.split('@')[0] || "N/A"} color="from-amber-500 to-orange-500" />
                    </div>
                  )}

                  <div className="glass-heavy rounded-2xl overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-white/5">
                        <tr>
                          <th className="text-left p-3 font-medium text-text-secondary">Admin</th>
                          <th className="text-left p-3 font-medium text-text-secondary">Action</th>
                          <th className="text-left p-3 font-medium text-text-secondary hidden md:table-cell">Target</th>
                          <th className="text-left p-3 font-medium text-text-secondary hidden lg:table-cell">Details</th>
                          <th className="text-right p-3 font-medium text-text-secondary">Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activityLogs.map(log => (
                          <tr key={log.id} className="border-t border-white/5">
                            <td className="p-3 text-text-secondary">{log.admin_email?.split('@')[0]}</td>
                            <td className="p-3">
                              <span className="px-2 py-1 rounded-full bg-white/10 text-xs">{log.action}</span>
                            </td>
                            <td className="p-3 text-text-secondary hidden md:table-cell">{log.target_type}</td>
                            <td className="p-3 text-text-secondary text-xs hidden lg:table-cell max-w-xs truncate">{log.details || "-"}</td>
                            <td className="p-3 text-right text-text-secondary text-xs">{new Date(log.timestamp).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-md glass-heavy rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold flex items-center gap-2"><Settings className="w-5 h-5 text-red-500" /> Update Credentials</h2>
              <Button onClick={() => setShowSettings(false)} variant="ghost" size="icon"><X className="w-5 h-5" /></Button>
            </div>
            <form onSubmit={handleUpdateCredentials} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Current Password *</label>
                <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required className="bg-white/5 border-white/10" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">New Email</label>
                <Input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} className="bg-white/5 border-white/10" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">New Username</label>
                <Input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} className="bg-white/5 border-white/10" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">New Password</label>
                <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="bg-white/5 border-white/10" />
              </div>
              <div className="flex gap-3 pt-2">
                <Button type="button" onClick={() => setShowSettings(false)} variant="ghost" className="flex-1">Cancel</Button>
                <Button type="submit" disabled={savingSettings} className="flex-1 bg-gradient-to-r from-red-500 to-orange-500">{savingSettings ? "Saving..." : "Save"}</Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Announcement Modal */}
      {showAnnouncementModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-lg glass-heavy rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">{editingAnnouncement ? 'Edit' : 'New'} Announcement</h2>
              <Button onClick={() => setShowAnnouncementModal(false)} variant="ghost" size="icon"><X className="w-5 h-5" /></Button>
            </div>
            <div className="space-y-4">
              <Input value={announcementForm.title} onChange={(e) => setAnnouncementForm(p => ({...p, title: e.target.value}))} placeholder="Title" className="bg-white/5 border-white/10" />
              <textarea value={announcementForm.message} onChange={(e) => setAnnouncementForm(p => ({...p, message: e.target.value}))} placeholder="Message" rows={3} className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 resize-none" />
              <div className="grid grid-cols-2 gap-3">
                <select value={announcementForm.type} onChange={(e) => setAnnouncementForm(p => ({...p, type: e.target.value}))} className="px-3 py-2 rounded-lg bg-white/5 border border-white/10">
                  <option value="info" className="bg-gray-900">Info</option>
                  <option value="warning" className="bg-gray-900">Warning</option>
                  <option value="success" className="bg-gray-900">Success</option>
                  <option value="error" className="bg-gray-900">Error</option>
                </select>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={announcementForm.is_active} onChange={(e) => setAnnouncementForm(p => ({...p, is_active: e.target.checked}))} className="w-4 h-4" />
                  <span className="text-sm">Active</span>
                </label>
              </div>
              <div className="flex gap-3 pt-2">
                <Button onClick={() => setShowAnnouncementModal(false)} variant="ghost" className="flex-1">Cancel</Button>
                <Button onClick={handleSaveAnnouncement} className="flex-1 bg-gradient-to-r from-yellow-500 to-orange-500">Save</Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Notification Modal */}
      {showNotificationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-lg glass-heavy rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Send Notification</h2>
              <Button onClick={() => setShowNotificationModal(false)} variant="ghost" size="icon"><X className="w-5 h-5" /></Button>
            </div>
            <div className="space-y-4">
              <Input value={notificationForm.user_id} onChange={(e) => setNotificationForm(p => ({...p, user_id: e.target.value}))} placeholder="User ID (leave empty for broadcast)" className="bg-white/5 border-white/10" />
              <Input value={notificationForm.title} onChange={(e) => setNotificationForm(p => ({...p, title: e.target.value}))} placeholder="Title" className="bg-white/5 border-white/10" />
              <textarea value={notificationForm.message} onChange={(e) => setNotificationForm(p => ({...p, message: e.target.value}))} placeholder="Message" rows={3} className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 resize-none" />
              <select value={notificationForm.type} onChange={(e) => setNotificationForm(p => ({...p, type: e.target.value}))} className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10">
                <option value="info" className="bg-gray-900">Info</option>
                <option value="warning" className="bg-gray-900">Warning</option>
                <option value="error" className="bg-gray-900">Error</option>
              </select>
              <div className="flex gap-3 pt-2">
                <Button onClick={() => setShowNotificationModal(false)} variant="ghost" className="flex-1">Cancel</Button>
                <Button onClick={handleSendNotification} className="flex-1 bg-gradient-to-r from-blue-500 to-purple-500">Send</Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Admin Modal */}
      {showAdminModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-md glass-heavy rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Create Admin</h2>
              <Button onClick={() => setShowAdminModal(false)} variant="ghost" size="icon"><X className="w-5 h-5" /></Button>
            </div>
            <div className="space-y-4">
              <Input value={adminForm.email} onChange={(e) => setAdminForm(p => ({...p, email: e.target.value}))} placeholder="Email" type="email" className="bg-white/5 border-white/10" />
              <Input value={adminForm.username} onChange={(e) => setAdminForm(p => ({...p, username: e.target.value}))} placeholder="Username" className="bg-white/5 border-white/10" />
              <Input value={adminForm.password} onChange={(e) => setAdminForm(p => ({...p, password: e.target.value}))} placeholder="Password" type="password" className="bg-white/5 border-white/10" />
              <select value={adminForm.role} onChange={(e) => setAdminForm(p => ({...p, role: e.target.value}))} className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10">
                <option value="moderator" className="bg-gray-900">Moderator</option>
                <option value="admin" className="bg-gray-900">Admin</option>
                <option value="super_admin" className="bg-gray-900">Super Admin</option>
              </select>
              <div className="flex gap-3 pt-2">
                <Button onClick={() => setShowAdminModal(false)} variant="ghost" className="flex-1">Cancel</Button>
                <Button onClick={handleCreateAdmin} className="flex-1 bg-gradient-to-r from-red-500 to-orange-500">Create</Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Chat View Modal */}
      {showChatModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-2xl glass-heavy rounded-2xl p-6 max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Chat Messages</h2>
              <div className="flex gap-2">
                <Button onClick={() => handleDeleteChat(selectedChat)} variant="ghost" className="text-red-400"><Trash2 className="w-4 h-4 mr-1" /> Delete All</Button>
                <Button onClick={() => setShowChatModal(false)} variant="ghost" size="icon"><X className="w-5 h-5" /></Button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto space-y-3">
              {chatMessages.map(msg => (
                <div key={msg.id} className={`p-3 rounded-xl max-w-[80%] ${msg.sender === 'user' ? 'ml-auto bg-blue-500/20' : 'bg-white/10'}`}>
                  <p className="text-xs text-text-muted mb-1">{msg.sender === 'user' ? 'User' : 'AI'}</p>
                  <p className="text-sm">{msg.content}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}

      {/* Character Edit Modal */}
      {showCharacterEditModal && editingCharacter && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-md glass-heavy rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Edit Character</h2>
              <Button onClick={() => setShowCharacterEditModal(false)} variant="ghost" size="icon"><X className="w-5 h-5" /></Button>
            </div>
            <div className="space-y-4">
              <Input value={characterForm.name} onChange={(e) => setCharacterForm(p => ({...p, name: e.target.value}))} placeholder="Name" className="bg-white/5 border-white/10" />
              <Input value={characterForm.age} onChange={(e) => setCharacterForm(p => ({...p, age: e.target.value}))} placeholder="Age" type="number" className="bg-white/5 border-white/10" />
              <Input value={characterForm.occupation} onChange={(e) => setCharacterForm(p => ({...p, occupation: e.target.value}))} placeholder="Occupation" className="bg-white/5 border-white/10" />
              <textarea value={characterForm.personality} onChange={(e) => setCharacterForm(p => ({...p, personality: e.target.value}))} placeholder="Personality" rows={2} className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 resize-none" />
              <textarea value={characterForm.description} onChange={(e) => setCharacterForm(p => ({...p, description: e.target.value}))} placeholder="Description" rows={2} className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 resize-none" />
              <div className="flex gap-3 pt-2">
                <Button onClick={() => setShowCharacterEditModal(false)} variant="ghost" className="flex-1">Cancel</Button>
                <Button onClick={handleSaveCharacter} className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500">Save</Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
