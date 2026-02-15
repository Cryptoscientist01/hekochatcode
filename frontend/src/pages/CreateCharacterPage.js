import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Wand2, Loader2, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PERSONALITY_TRAITS = [
  "Friendly", "Playful", "Caring", "Adventurous", "Mysterious", 
  "Intellectual", "Romantic", "Confident", "Shy", "Energetic",
  "Calm", "Witty", "Supportive", "Bold", "Creative"
];

export default function CreateCharacterPage({ user }) {
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    age: 25,
    personality: "",
    description: "",
    occupation: "",
    traits: [],
    avatarPrompt: ""
  });

  const handleTraitToggle = (trait) => {
    if (formData.traits.includes(trait)) {
      setFormData({
        ...formData,
        traits: formData.traits.filter(t => t !== trait)
      });
    } else if (formData.traits.length < 5) {
      setFormData({
        ...formData,
        traits: [...formData.traits, trait]
      });
    } else {
      toast.error("Maximum 5 traits allowed");
    }
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      toast.error("Please enter a name");
      return;
    }
    if (!formData.personality.trim()) {
      toast.error("Please describe the personality");
      return;
    }
    if (!formData.description.trim()) {
      toast.error("Please add a description");
      return;
    }
    if (formData.traits.length === 0) {
      toast.error("Please select at least one trait");
      return;
    }

    setCreating(true);

    try {
      const response = await axios.post(`${API}/characters/create`, {
        user_id: user.id,
        name: formData.name.trim(),
        age: formData.age,
        personality: formData.personality.trim(),
        description: formData.description.trim(),
        occupation: formData.occupation.trim() || null,
        traits: formData.traits,
        avatar_prompt: formData.avatarPrompt.trim() || null
      });

      toast.success("Character created successfully!");
      navigate(`/chat/${response.data.character.id}`);
    } catch (error) {
      toast.error("Failed to create character. Please try again.");
      console.error(error);
    } finally {
      setCreating(false);
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
              <h1 className="text-xl font-heading font-bold">Create Character</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-heavy rounded-2xl p-8"
          >
            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-heading font-bold">Create Your AI Companion</h2>
              <p className="text-text-secondary mt-2">Design a unique character to chat with</p>
            </div>

            <div className="space-y-6">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Name *
                </label>
                <Input
                  data-testid="char-name-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Give your character a name"
                  className="bg-white/5 border-white/10 focus:border-primary rounded-xl p-4 text-white placeholder:text-white/30"
                />
              </div>

              {/* Age */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Age
                </label>
                <Input
                  data-testid="char-age-input"
                  type="number"
                  min="18"
                  max="99"
                  value={formData.age}
                  onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || 25 })}
                  className="bg-white/5 border-white/10 focus:border-primary rounded-xl p-4 text-white w-32"
                />
              </div>

              {/* Occupation */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Occupation (optional)
                </label>
                <Input
                  data-testid="char-occupation-input"
                  value={formData.occupation}
                  onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                  placeholder="e.g., Artist, Student, Chef"
                  className="bg-white/5 border-white/10 focus:border-primary rounded-xl p-4 text-white placeholder:text-white/30"
                />
              </div>

              {/* Personality Traits */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Personality Traits * (select up to 5)
                </label>
                <div className="flex flex-wrap gap-2">
                  {PERSONALITY_TRAITS.map((trait) => (
                    <button
                      key={trait}
                      data-testid={`trait-${trait.toLowerCase()}`}
                      onClick={() => handleTraitToggle(trait)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                        formData.traits.includes(trait)
                          ? 'bg-primary text-white'
                          : 'bg-white/5 border border-white/10 text-text-secondary hover:border-primary/50'
                      }`}
                    >
                      {trait}
                    </button>
                  ))}
                </div>
              </div>

              {/* Personality Description */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Personality Description *
                </label>
                <textarea
                  data-testid="char-personality-input"
                  value={formData.personality}
                  onChange={(e) => setFormData({ ...formData, personality: e.target.value })}
                  placeholder="Describe how your character behaves, speaks, and interacts..."
                  rows={3}
                  className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl p-4 text-white placeholder:text-white/30 resize-none"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Character Bio *
                </label>
                <textarea
                  data-testid="char-description-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Write a short bio that will be shown on the character card..."
                  rows={3}
                  className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl p-4 text-white placeholder:text-white/30 resize-none"
                />
              </div>

              {/* Avatar Prompt */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Avatar Description (optional - AI will generate)
                </label>
                <textarea
                  data-testid="char-avatar-input"
                  value={formData.avatarPrompt}
                  onChange={(e) => setFormData({ ...formData, avatarPrompt: e.target.value })}
                  placeholder="Describe how your character looks... e.g., 'A young woman with long brown hair, green eyes, and a warm smile'"
                  rows={2}
                  className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl p-4 text-white placeholder:text-white/30 resize-none"
                />
                <p className="text-xs text-text-muted mt-2">
                  Leave empty to use a default avatar, or describe for AI-generated portrait
                </p>
              </div>

              {/* Create Button */}
              <Button
                data-testid="create-char-btn"
                onClick={handleCreate}
                disabled={creating}
                className="w-full bg-gradient-to-r from-primary to-accent-purple hover:from-primary/90 hover:to-accent-purple/90 text-white rounded-xl py-6 font-bold shadow-neon mt-4"
              >
                {creating ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Creating Character...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-5 h-5 mr-2" />
                    Create Character
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
