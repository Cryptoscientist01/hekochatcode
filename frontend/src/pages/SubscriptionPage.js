import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Crown, Check, Sparkles, Zap, Shield, Star, MessageCircle, Image as ImageIcon, Mic } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function SubscriptionPage({ user }) {
  const navigate = useNavigate();
  const [selectedPlan, setSelectedPlan] = useState("premium");
  const [billingCycle, setBillingCycle] = useState("yearly");

  const plans = {
    free: {
      name: "Free",
      icon: Star,
      price: { monthly: 0, yearly: 0 },
      color: "from-gray-500 to-gray-600",
      features: [
        "5 messages per day",
        "Basic AI responses",
        "Access to 5 characters",
        "Standard response time"
      ],
      limitations: [
        "No image generation",
        "No voice messages",
        "No custom characters"
      ]
    },
    premium: {
      name: "Premium",
      icon: Crown,
      price: { monthly: 9.99, yearly: 59.99 },
      color: "from-primary to-accent-purple",
      popular: true,
      features: [
        "Unlimited messages",
        "Advanced AI personalities",
        "Access to all 25+ characters",
        "Priority response time",
        "10 image generations/day",
        "Voice message playback",
        "Create up to 5 custom characters"
      ],
      limitations: []
    },
    ultimate: {
      name: "Ultimate",
      icon: Zap,
      price: { monthly: 19.99, yearly: 119.99 },
      color: "from-amber-500 to-orange-500",
      features: [
        "Everything in Premium",
        "Unlimited image generation",
        "Unlimited custom characters",
        "Early access to new features",
        "Exclusive character collection",
        "Priority support",
        "Custom voice selection",
        "API access"
      ],
      limitations: []
    }
  };

  const handleSubscribe = (plan) => {
    toast.success(`${plan.name} plan selected! Payment integration coming soon.`);
  };

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
              <h1 className="text-xl font-heading font-bold">Subscription</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Hero Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm text-primary font-medium">Limited Time: 50% OFF Annual Plans</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-heading font-bold mb-4">
              Upgrade Your <span className="text-primary">Experience</span>
            </h1>
            <p className="text-text-secondary text-lg max-w-2xl mx-auto">
              Unlock unlimited conversations, custom characters, and exclusive features
            </p>
          </motion.div>

          {/* Billing Toggle */}
          <div className="flex justify-center mb-10">
            <div className="flex items-center gap-2 p-1 rounded-full glass-heavy">
              <button
                data-testid="billing-monthly"
                onClick={() => setBillingCycle("monthly")}
                className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
                  billingCycle === "monthly"
                    ? "bg-primary text-white"
                    : "text-text-secondary hover:text-white"
                }`}
              >
                Monthly
              </button>
              <button
                data-testid="billing-yearly"
                onClick={() => setBillingCycle("yearly")}
                className={`px-6 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                  billingCycle === "yearly"
                    ? "bg-primary text-white"
                    : "text-text-secondary hover:text-white"
                }`}
              >
                Yearly
                <span className="px-2 py-0.5 bg-green-500 text-white text-xs rounded-full">Save 50%</span>
              </button>
            </div>
          </div>

          {/* Pricing Cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {Object.entries(plans).map(([key, plan], index) => {
              const Icon = plan.icon;
              const price = plan.price[billingCycle];
              const isSelected = selectedPlan === key;
              
              return (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  data-testid={`plan-${key}`}
                  onClick={() => setSelectedPlan(key)}
                  className={`relative rounded-2xl p-6 cursor-pointer transition-all duration-300 ${
                    isSelected
                      ? "glass-heavy border-2 border-primary scale-105"
                      : "glass border border-white/10 hover:border-white/20"
                  } ${plan.popular ? "md:-translate-y-4" : ""}`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-4 py-1 bg-gradient-to-r from-primary to-accent-purple text-white text-xs font-bold rounded-full">
                        MOST POPULAR
                      </span>
                    </div>
                  )}

                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${plan.color} flex items-center justify-center mb-4`}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>

                  <h3 className="text-2xl font-heading font-bold mb-2">{plan.name}</h3>
                  
                  <div className="mb-6">
                    <span className="text-4xl font-bold">${price}</span>
                    <span className="text-text-secondary">/{billingCycle === "yearly" ? "year" : "month"}</span>
                    {billingCycle === "yearly" && price > 0 && (
                      <p className="text-sm text-green-400 mt-1">
                        ${(price / 12).toFixed(2)}/month billed annually
                      </p>
                    )}
                  </div>

                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                    {plan.limitations.map((limitation, i) => (
                      <li key={i} className="flex items-start gap-3 text-text-muted">
                        <span className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                          <span className="w-1.5 h-1.5 bg-text-muted rounded-full" />
                        </span>
                        <span className="text-sm line-through">{limitation}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    data-testid={`subscribe-${key}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSubscribe(plan);
                    }}
                    className={`w-full ${
                      key === "free"
                        ? "bg-white/10 hover:bg-white/20 text-white"
                        : `bg-gradient-to-r ${plan.color} hover:opacity-90`
                    }`}
                  >
                    {key === "free" ? "Current Plan" : `Get ${plan.name}`}
                  </Button>
                </motion.div>
              );
            })}
          </div>

          {/* Features Comparison */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-heavy rounded-2xl p-8"
          >
            <h2 className="text-2xl font-heading font-bold mb-8 text-center">
              What You <span className="text-primary">Get</span>
            </h2>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mx-auto mb-4">
                  <MessageCircle className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-bold mb-2">Unlimited Chat</h3>
                <p className="text-text-secondary text-sm">
                  Chat with your AI companions anytime, without limits. Experience natural conversations with advanced AI personalities.
                </p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center mx-auto mb-4">
                  <ImageIcon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-bold mb-2">Image Generation</h3>
                <p className="text-text-secondary text-sm">
                  Create stunning AI-generated images with your characters. Visualize any scenario you can imagine.
                </p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center mx-auto mb-4">
                  <Mic className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-bold mb-2">Voice Messages</h3>
                <p className="text-text-secondary text-sm">
                  Hear your AI companions speak with natural voice synthesis. Multiple voice options available.
                </p>
              </div>
            </div>
          </motion.div>

          {/* Trust Badges */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-12 flex flex-wrap justify-center items-center gap-8"
          >
            <div className="flex items-center gap-2 text-text-secondary">
              <Shield className="w-5 h-5" />
              <span className="text-sm">Secure Payment</span>
            </div>
            <div className="flex items-center gap-2 text-text-secondary">
              <Check className="w-5 h-5" />
              <span className="text-sm">Cancel Anytime</span>
            </div>
            <div className="flex items-center gap-2 text-text-secondary">
              <Star className="w-5 h-5" />
              <span className="text-sm">30-Day Money Back</span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
