import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Crown, Check, Sparkles, Zap, Shield, Star, MessageCircle, Image as ImageIcon, Mic, CreditCard, Loader2 } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SubscriptionPage({ user, token }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [selectedPlan, setSelectedPlan] = useState("premium");
  const [billingCycle, setBillingCycle] = useState("yearly");
  const [loading, setLoading] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState(null);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState("stripe");

  const plans = {
    free: {
      name: "Free",
      icon: Star,
      price: { monthly: 0, yearly: 0 },
      planId: { monthly: "free", yearly: "free" },
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
      planId: { monthly: "premium_monthly", yearly: "premium_yearly" },
      color: "from-primary to-accent-purple",
      popular: true,
      features: [
        "Unlimited messages",
        "Advanced AI personalities",
        "Access to all characters",
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
      planId: { monthly: "ultimate_monthly", yearly: "ultimate_yearly" },
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

  // Fetch current subscription
  useEffect(() => {
    const fetchSubscription = async () => {
      if (!token) return;
      try {
        const res = await fetch(`${API}/payments/user-subscription`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setCurrentSubscription(data);
        }
      } catch (error) {
        console.error("Failed to fetch subscription:", error);
      }
    };
    fetchSubscription();
  }, [token]);

  // Check for cancelled payment
  useEffect(() => {
    if (searchParams.get("cancelled") === "true") {
      toast.error("Payment was cancelled. Feel free to try again when you're ready!");
    }
  }, [searchParams]);

  const handleSubscribe = async (planKey) => {
    if (planKey === "free") {
      toast.info("You're already on the free plan!");
      return;
    }

    if (!user || !token) {
      toast.error("Please sign in to subscribe");
      navigate("/auth");
      return;
    }

    const plan = plans[planKey];
    const planId = plan.planId[billingCycle];

    setLoadingPlan(planKey);
    setLoading(true);

    try {
      const res = await fetch(`${API}/payments/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          plan_id: planId,
          origin_url: window.location.origin,
          payment_method: paymentMethod
        })
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to create checkout session");
      }

      const data = await res.json();
      
      if (data.note) {
        toast.info(data.note);
      }

      // Redirect to payment provider
      window.location.href = data.checkout_url;
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error(error.message || "Failed to start checkout. Please try again.");
      setLoading(false);
      setLoadingPlan(null);
    }
  };

  const isCurrentPlan = useCallback((planKey) => {
    if (!currentSubscription?.has_subscription) {
      return planKey === "free";
    }
    const subPlanId = currentSubscription?.subscription?.plan_id || "";
    return subPlanId.startsWith(planKey);
  }, [currentSubscription]);

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

          {/* Payment Method Toggle */}
          <div className="flex justify-center mb-6">
            <div className="flex items-center gap-2 p-1 rounded-full glass-heavy">
              <button
                data-testid="payment-stripe"
                onClick={() => setPaymentMethod("stripe")}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                  paymentMethod === "stripe"
                    ? "bg-primary text-white"
                    : "text-text-secondary hover:text-white"
                }`}
              >
                <CreditCard className="w-4 h-4" />
                Stripe
              </button>
              <button
                data-testid="payment-paypal"
                onClick={() => setPaymentMethod("paypal")}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                  paymentMethod === "paypal"
                    ? "bg-blue-500 text-white"
                    : "text-text-secondary hover:text-white"
                }`}
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944 3.72a.775.775 0 0 1 .764-.654h6.751c2.241 0 4.12.612 5.135 1.747.473.528.803 1.138.973 1.813.174.695.18 1.48.014 2.383-.017.09-.035.178-.055.266l-.003.01v.076c-.38 2.45-1.614 4.03-3.556 4.79-.927.363-2.01.539-3.228.539H9.993a.955.955 0 0 0-.943.81l-.741 4.718-.004.028L7.076 21.337z"/>
                </svg>
                PayPal
              </button>
            </div>
          </div>

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
              const isCurrent = isCurrentPlan(key);
              const isLoading = loadingPlan === key;
              
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

                  {isCurrent && (
                    <div className="absolute -top-3 right-4">
                      <span className="px-3 py-1 bg-green-500 text-white text-xs font-bold rounded-full">
                        CURRENT
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
                      handleSubscribe(key);
                    }}
                    disabled={loading || isCurrent}
                    className={`w-full ${
                      key === "free" || isCurrent
                        ? "bg-white/10 hover:bg-white/20 text-white"
                        : `bg-gradient-to-r ${plan.color} hover:opacity-90`
                    }`}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : isCurrent ? (
                      "Current Plan"
                    ) : key === "free" ? (
                      "Free Tier"
                    ) : (
                      `Get ${plan.name}`
                    )}
                  </Button>
                </motion.div>
              );
            })}
          </div>

          {/* Payment Methods Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-xl p-6 mb-8"
          >
            <h3 className="text-lg font-bold mb-4 text-center">Secure Payment Options</h3>
            <div className="flex flex-wrap justify-center items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="w-10 h-6 bg-gradient-to-r from-blue-600 to-blue-400 rounded flex items-center justify-center">
                  <span className="text-white text-xs font-bold">VISA</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-10 h-6 bg-gradient-to-r from-red-500 to-orange-400 rounded flex items-center justify-center">
                  <span className="text-white text-xs font-bold">MC</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-10 h-6 bg-gradient-to-r from-blue-800 to-blue-600 rounded flex items-center justify-center">
                  <span className="text-white text-xs font-bold">AMEX</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-10 h-6 bg-[#003087] rounded flex items-center justify-center">
                  <span className="text-white text-xs font-bold">PP</span>
                </div>
              </div>
            </div>
          </motion.div>

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
