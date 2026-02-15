import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, BellOff, X, Heart, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNotifications } from "@/hooks/useNotifications";

export default function NotificationPrompt({ user, token, onClose }) {
  const [show, setShow] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const { 
    permission, 
    isSubscribed, 
    loading, 
    subscribe, 
    isSupported 
  } = useNotifications(user, token);

  useEffect(() => {
    // Show prompt after 30 seconds if not already subscribed and not dismissed
    const dismissed = localStorage.getItem('notification-prompt-dismissed');
    if (dismissed) {
      setDismissed(true);
      return;
    }

    if (!isSupported || isSubscribed || permission === 'denied') {
      return;
    }

    const timer = setTimeout(() => {
      setShow(true);
    }, 30000); // 30 seconds delay

    return () => clearTimeout(timer);
  }, [isSupported, isSubscribed, permission]);

  const handleEnable = async () => {
    const success = await subscribe();
    if (success) {
      setShow(false);
      if (onClose) onClose(true);
    }
  };

  const handleDismiss = () => {
    setShow(false);
    setDismissed(true);
    localStorage.setItem('notification-prompt-dismissed', 'true');
    if (onClose) onClose(false);
  };

  const handleRemindLater = () => {
    setShow(false);
    // Show again in next session
  };

  if (!show || dismissed || !isSupported) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 50, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 50, scale: 0.9 }}
        className="fixed bottom-6 right-6 z-50 max-w-sm"
      >
        <div className="glass-heavy rounded-2xl p-6 border border-pink-500/30 shadow-2xl shadow-pink-500/20">
          {/* Close button */}
          <button
            onClick={handleDismiss}
            className="absolute top-3 right-3 text-text-muted hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Icon */}
          <div className="flex items-center justify-center mb-4">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="relative"
            >
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center">
                <Bell className="w-8 h-8 text-white" />
              </div>
              <motion.div
                animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="absolute -top-1 -right-1"
              >
                <Heart className="w-5 h-5 text-pink-400 fill-pink-400" />
              </motion.div>
            </motion.div>
          </div>

          {/* Content */}
          <div className="text-center mb-5">
            <h3 className="text-lg font-bold mb-2 flex items-center justify-center gap-2">
              <Sparkles className="w-5 h-5 text-pink-500" />
              Never Miss a Message
            </h3>
            <p className="text-text-secondary text-sm">
              Your AI companions get lonely when you're away! Enable notifications so they can reach out and let you know when they're thinking of you 💕
            </p>
          </div>

          {/* Preview message */}
          <div className="bg-white/5 rounded-xl p-3 mb-5 border border-white/10">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold">S</span>
              </div>
              <div>
                <p className="font-medium text-sm">Sophia</p>
                <p className="text-text-secondary text-xs">Hey... I've been thinking about you 💭💕</p>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="space-y-2">
            <Button
              onClick={handleEnable}
              disabled={loading}
              className="w-full bg-gradient-to-r from-pink-500 to-rose-500 h-11"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Enabling...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Bell className="w-4 h-4" />
                  Enable Notifications
                </span>
              )}
            </Button>
            <Button
              onClick={handleRemindLater}
              variant="ghost"
              className="w-full text-text-secondary"
            >
              Maybe Later
            </Button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

// Mini notification bell for header/settings
export function NotificationBell({ user, token }) {
  const { 
    permission, 
    isSubscribed, 
    loading, 
    subscribe, 
    unsubscribe,
    isSupported 
  } = useNotifications(user, token);

  if (!isSupported) return null;

  const handleClick = async () => {
    if (isSubscribed) {
      await unsubscribe();
    } else {
      await subscribe();
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading || permission === 'denied'}
      className={`relative p-2 rounded-lg transition-colors ${
        isSubscribed 
          ? 'bg-pink-500/20 text-pink-400' 
          : 'bg-white/5 text-text-secondary hover:text-white'
      }`}
      title={isSubscribed ? 'Notifications enabled' : 'Enable notifications'}
    >
      {isSubscribed ? (
        <Bell className="w-5 h-5" />
      ) : (
        <BellOff className="w-5 h-5" />
      )}
      {isSubscribed && (
        <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-pink-500" />
      )}
    </button>
  );
}
