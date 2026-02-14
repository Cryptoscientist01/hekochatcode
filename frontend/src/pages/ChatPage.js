import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Heart, ArrowLeft, Send, Mic, Image as ImageIcon, Volume2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ChatPage({ user, onLogout }) {
  const navigate = useNavigate();
  const { characterId } = useParams();
  const [character, setCharacter] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingVoice, setLoadingVoice] = useState(false);
  const [loadingImage, setLoadingImage] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchCharacter();
    fetchChatHistory();
  }, [characterId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchCharacter = async () => {
    try {
      const response = await axios.get(`${API}/characters/${characterId}`);
      setCharacter(response.data);
    } catch (error) {
      toast.error("Failed to load character");
      navigate('/characters');
    }
  };

  const fetchChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/history/${characterId}?user_id=${user.id}`);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error("Failed to load chat history", error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: "user",
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages([...messages, userMsg]);
    setInputMessage("");
    setLoading(true);

    try {
      const response = await axios.post(`${API}/chat/send`, {
        character_id: characterId,
        user_id: user.id,
        message: inputMessage
      });

      const aiMsg = {
        id: response.data.message_id,
        sender: "ai",
        content: response.data.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      toast.error("Failed to send message");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateVoice = async (text) => {
    setLoadingVoice(true);
    try {
      const response = await axios.post(`${API}/voice/generate`, {
        text: text,
        voice: "nova"
      });

      // Create audio element and play
      const audio = new Audio(`data:audio/mp3;base64,${response.data.audio}`);
      audio.play();
      toast.success("Playing voice message");
    } catch (error) {
      toast.error("Failed to generate voice");
    } finally {
      setLoadingVoice(false);
    }
  };

  const handleGenerateImage = async () => {
    const prompt = window.prompt("Describe the image you want to generate:");
    if (!prompt) return;

    setLoadingImage(true);
    try {
      const response = await axios.post(`${API}/image/generate`, {
        prompt: prompt,
        character_id: characterId
      });

      const imageMsg = {
        id: Date.now().toString(),
        sender: "ai",
        content: "Here's the image you requested!",
        image: response.data.image,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, imageMsg]);
      toast.success("Image generated!");
    } catch (error) {
      toast.error("Failed to generate image");
    } finally {
      setLoadingImage(false);
    }
  };

  if (!character) {
    return <div className="min-h-screen bg-background flex items-center justify-center text-white">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-heavy">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button
              data-testid="back-to-characters-btn"
              onClick={() => navigate('/characters')}
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10"
            >
              <ArrowLeft className="w-6 h-6" />
            </Button>
            <div className="flex items-center gap-3">
              <img
                src={character.avatar_url}
                alt={character.name}
                className="w-12 h-12 rounded-full object-cover border-2 border-primary"
              />
              <div>
                <h2 className="font-heading font-bold text-lg">{character.name}</h2>
                <p className="text-xs text-text-secondary">Online</p>
              </div>
            </div>
          </div>
          
          <Button
            data-testid="logout-btn"
            onClick={onLogout}
            variant="outline"
            className="border-white/20 text-white hover:bg-white/10 rounded-full px-6"
          >
            Logout
          </Button>
        </div>
      </nav>

      {/* Chat Messages */}
      <div className="flex-1 pt-24 pb-32 px-6 overflow-y-auto">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-text-secondary py-12">
              <p>Start a conversation with {character.name}!</p>
            </div>
          )}

          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[70%] ${msg.sender === 'user' ? 'order-2' : 'order-1'}`}>
                <div
                  data-testid={`message-${msg.id}`}
                  className={`p-4 rounded-2xl ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-r from-primary to-accent-purple text-white rounded-tr-sm'
                      : 'glass-heavy rounded-tl-sm'
                  }`}
                >
                  <p className="text-base">{msg.content}</p>
                  {msg.image && (
                    <img
                      src={`data:image/png;base64,${msg.image}`}
                      alt="Generated"
                      className="mt-3 rounded-xl max-w-full"
                    />
                  )}
                </div>
                
                {msg.sender === 'ai' && (
                  <button
                    data-testid={`voice-btn-${msg.id}`}
                    onClick={() => handleGenerateVoice(msg.content)}
                    disabled={loadingVoice}
                    className="mt-2 text-xs text-primary hover:text-primary/80 flex items-center gap-1"
                  >
                    <Volume2 className="w-3 h-3" />
                    {loadingVoice ? 'Generating...' : 'Play voice'}
                  </button>
                )}
              </div>
            </motion.div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="glass-heavy p-4 rounded-2xl rounded-tl-sm">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Bar */}
      <div className="fixed bottom-0 w-full glass-heavy border-t border-white/10">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <form onSubmit={handleSendMessage} className="flex items-center gap-3">
            <Button
              data-testid="generate-image-btn"
              type="button"
              onClick={handleGenerateImage}
              disabled={loadingImage}
              variant="ghost"
              size="icon"
              className="text-secondary hover:bg-secondary/10"
            >
              <ImageIcon className="w-5 h-5" />
            </Button>
            
            <Input
              data-testid="message-input"
              type="text"
              placeholder={`Message ${character.name}...`}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              className="flex-1 bg-white/5 border-white/10 focus:border-primary focus:ring-1 focus:ring-primary rounded-full px-6 py-6 text-white placeholder:text-white/30"
              disabled={loading}
            />
            
            <Button
              data-testid="send-message-btn"
              type="submit"
              disabled={loading || !inputMessage.trim()}
              className="bg-primary hover:bg-primary/90 rounded-full p-6"
            >
              <Send className="w-5 h-5" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}