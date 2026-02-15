import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Wand2, Download, Trash2, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STYLES = [
  { id: "realistic", name: "Realistic", emoji: "📷" },
  { id: "anime", name: "Anime", emoji: "🎨" },
  { id: "artistic", name: "Artistic", emoji: "🖼️" },
  { id: "fantasy", name: "Fantasy", emoji: "✨" }
];

export default function GenerateImagePage({ user }) {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState("realistic");
  const [generating, setGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [myImages, setMyImages] = useState([]);
  const [loadingImages, setLoadingImages] = useState(true);

  useEffect(() => {
    fetchMyImages();
  }, []);

  const fetchMyImages = async () => {
    try {
      const response = await axios.get(`${API}/images/my/${user.id}`);
      setMyImages(response.data.images || []);
    } catch (error) {
      console.error("Failed to load images", error);
    } finally {
      setLoadingImages(false);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error("Please enter a prompt");
      return;
    }

    setGenerating(true);
    setGeneratedImage(null);

    try {
      const response = await axios.post(`${API}/images/generate`, {
        user_id: user.id,
        prompt: prompt.trim(),
        style
      });

      setGeneratedImage({
        id: response.data.id,
        image: response.data.image,
        mime_type: response.data.mime_type,
        prompt: response.data.prompt
      });

      // Add to my images list
      setMyImages(prev => [{
        id: response.data.id,
        image_data: response.data.image,
        mime_type: response.data.mime_type,
        prompt: response.data.prompt,
        style,
        created_at: new Date().toISOString()
      }, ...prev]);

      toast.success("Image generated successfully!");
    } catch (error) {
      toast.error("Failed to generate image. Please try again.");
      console.error(error);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = (imageData, mimeType, filename) => {
    const link = document.createElement('a');
    link.href = `data:${mimeType};base64,${imageData}`;
    link.download = filename || 'ai-generated-image.png';
    link.click();
  };

  const handleDelete = async (imageId) => {
    try {
      await axios.delete(`${API}/images/${imageId}?user_id=${user.id}`);
      setMyImages(myImages.filter(img => img.id !== imageId));
      if (generatedImage?.id === imageId) {
        setGeneratedImage(null);
      }
      toast.success("Image deleted");
    } catch (error) {
      toast.error("Failed to delete image");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <nav className="fixed top-0 w-full z-50 glass-heavy border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => navigate('/characters')}
                variant="ghost"
                className="text-text-secondary hover:text-white"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Back
              </Button>
              <h1 className="text-xl font-heading font-bold">Generate Image</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Generator Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-heavy rounded-2xl p-8 mb-12"
          >
            <h2 className="text-2xl font-heading font-bold mb-6 flex items-center gap-3">
              <Wand2 className="w-6 h-6 text-primary" />
              AI Image Generator
            </h2>

            {/* Prompt Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Describe your image
              </label>
              <Input
                data-testid="image-prompt-input"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="A beautiful sunset over mountains with a lake in the foreground..."
                className="bg-white/5 border-white/10 focus:border-primary rounded-xl p-4 text-white placeholder:text-white/30"
              />
            </div>

            {/* Style Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-text-secondary mb-3">
                Style
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {STYLES.map((s) => (
                  <button
                    key={s.id}
                    data-testid={`style-${s.id}`}
                    onClick={() => setStyle(s.id)}
                    className={`p-4 rounded-xl border transition-all ${
                      style === s.id
                        ? 'border-primary bg-primary/20 text-white'
                        : 'border-white/10 bg-white/5 text-text-secondary hover:border-white/20'
                    }`}
                  >
                    <span className="text-2xl mb-2 block">{s.emoji}</span>
                    <span className="text-sm font-medium">{s.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <Button
              data-testid="generate-btn"
              onClick={handleGenerate}
              disabled={generating || !prompt.trim()}
              className="w-full bg-gradient-to-r from-primary to-accent-purple hover:from-primary/90 hover:to-accent-purple/90 text-white rounded-xl py-6 font-bold shadow-neon"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Wand2 className="w-5 h-5 mr-2" />
                  Generate Image
                </>
              )}
            </Button>

            {/* Generated Image Preview */}
            {generatedImage && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mt-8"
              >
                <div className="relative rounded-xl overflow-hidden">
                  <img
                    src={`data:${generatedImage.mime_type};base64,${generatedImage.image}`}
                    alt={generatedImage.prompt}
                    className="w-full h-auto"
                  />
                  <div className="absolute bottom-4 right-4 flex gap-2">
                    <Button
                      onClick={() => handleDownload(generatedImage.image, generatedImage.mime_type, `ai-image-${Date.now()}.png`)}
                      className="glass-heavy hover:bg-white/20"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </div>
                <p className="text-sm text-text-secondary mt-3">"{generatedImage.prompt}"</p>
              </motion.div>
            )}
          </motion.div>

          {/* My Images Gallery */}
          <div>
            <h3 className="text-xl font-heading font-bold mb-6">My Generated Images</h3>
            
            {loadingImages ? (
              <div className="flex justify-center py-10">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : myImages.length === 0 ? (
              <div className="text-center py-10 text-text-secondary">
                <Wand2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No images generated yet</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {myImages.map((img, index) => (
                  <motion.div
                    key={img.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="relative group rounded-xl overflow-hidden"
                  >
                    <img
                      src={`data:${img.mime_type};base64,${img.image_data}`}
                      alt={img.prompt}
                      className="w-full aspect-square object-cover"
                    />
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleDownload(img.image_data, img.mime_type, `ai-image-${img.id}.png`)}
                        className="glass-heavy hover:bg-white/20"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleDelete(img.id)}
                        className="glass-heavy hover:bg-red-500/20 text-red-400"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
