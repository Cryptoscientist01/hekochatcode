import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import CharactersPage from "./pages/CharactersPage";
import ChatPage from "./pages/ChatPage";
import CollectionPage from "./pages/CollectionPage";
import GenerateImagePage from "./pages/GenerateImagePage";
import CreateCharacterPage from "./pages/CreateCharacterPage";
import MyAIPage from "./pages/MyAIPage";
import SubscriptionPage from "./pages/SubscriptionPage";
import ProfilePage from "./pages/ProfilePage";
import SettingsPage from "./pages/SettingsPage";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth callback component to handle Google OAuth redirect
function AuthCallback({ onAuth }) {
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = { current: false };

  useEffect(() => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processSession = async () => {
      const hash = location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);
      
      if (sessionIdMatch) {
        const sessionId = sessionIdMatch[1];
        
        try {
          const response = await fetch(`${API}/auth/google/session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId }),
            credentials: 'include'
          });
          
          if (response.ok) {
            const data = await response.json();
            onAuth(data.token, data.user);
            navigate('/characters', { replace: true, state: { user: data.user } });
          } else {
            navigate('/auth', { replace: true });
          }
        } catch (error) {
          console.error('Auth callback error:', error);
          navigate('/auth', { replace: true });
        }
      } else {
        navigate('/auth', { replace: true });
      }
    };

    processSession();
  }, []);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-white text-xl">Signing you in...</div>
    </div>
  );
}

function AppRouter({ user, setUser, setToken }) {
  const location = useLocation();

  const handleAuth = (authToken, authUser) => {
    setToken(authToken);
    setUser(authUser);
    localStorage.setItem('token', authToken);
    localStorage.setItem('user', JSON.stringify(authUser));
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  // Check URL fragment for session_id (Google OAuth callback)
  // This check happens synchronously during render to prevent race conditions
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback onAuth={handleAuth} />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage user={user} onLogout={handleLogout} />} />
      <Route 
        path="/auth" 
        element={
          user ? <Navigate to="/characters" /> : <AuthPage onAuth={handleAuth} />
        } 
      />
      <Route 
        path="/characters" 
        element={
          user ? <CharactersPage user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/characters/:category" 
        element={
          user ? <CharactersPage user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/chat/:characterId" 
        element={
          user ? <ChatPage user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/collection" 
        element={
          user ? <CollectionPage user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/generate-image" 
        element={
          user ? <GenerateImagePage user={user} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/create-character" 
        element={
          user ? <CreateCharacterPage user={user} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/my-ai" 
        element={
          user ? <MyAIPage user={user} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/subscription" 
        element={
          user ? <SubscriptionPage user={user} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/profile" 
        element={
          user ? <ProfilePage user={user} onUpdateUser={setUser} /> : <Navigate to="/auth" />
        } 
      />
      <Route 
        path="/settings" 
        element={
          user ? <SettingsPage user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />
        } 
      />
    </Routes>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
  }, []);

  return (
    <div className="App min-h-screen bg-background">
      <BrowserRouter>
        <AppRouter user={user} setUser={setUser} setToken={setToken} />
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;