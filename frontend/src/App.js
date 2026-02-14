import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import CharactersPage from "./pages/CharactersPage";
import ChatPage from "./pages/ChatPage";
import { Toaster } from "@/components/ui/sonner";

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

  const handleAuth = (authToken, authUser) => {
    setToken(authToken);
    setUser(authUser);
    localStorage.setItem('token', authToken);
    localStorage.setItem('user', JSON.stringify(authUser));
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <div className="App min-h-screen bg-background">
      <BrowserRouter>
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
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;