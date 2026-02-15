import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle, XCircle, Loader2, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import confetti from 'canvas-confetti';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PaymentSuccessPage({ token }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("loading");
  const [paymentDetails, setPaymentDetails] = useState(null);
  const [pollCount, setPollCount] = useState(0);

  const sessionId = searchParams.get("session_id");
  const maxPolls = 5;
  const pollInterval = 2000;

  useEffect(() => {
    if (!sessionId) {
      setStatus("error");
      return;
    }

    const checkPaymentStatus = async () => {
      try {
        const res = await fetch(`${API}/payments/status/${sessionId}?payment_method=stripe`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });

        if (!res.ok) {
          throw new Error("Failed to check payment status");
        }

        const data = await res.json();
        setPaymentDetails(data);

        if (data.payment_status === "paid") {
          setStatus("success");
          // Trigger confetti!
          confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
          });
        } else if (data.status === "expired") {
          setStatus("expired");
        } else if (pollCount < maxPolls) {
          // Continue polling
          setTimeout(() => setPollCount(c => c + 1), pollInterval);
        } else {
          // Max polls reached, show pending
          setStatus("pending");
        }
      } catch (error) {
        console.error("Payment status check failed:", error);
        if (pollCount < maxPolls) {
          setTimeout(() => setPollCount(c => c + 1), pollInterval);
        } else {
          setStatus("error");
        }
      }
    };

    checkPaymentStatus();
  }, [sessionId, pollCount, token]);

  const renderContent = () => {
    switch (status) {
      case "loading":
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center"
          >
            <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-6">
              <Loader2 className="w-10 h-10 text-primary animate-spin" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Processing Payment...</h1>
            <p className="text-text-secondary">Please wait while we confirm your payment.</p>
          </motion.div>
        );

      case "success":
        return (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <div className="w-24 h-24 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-14 h-14 text-green-500" />
            </div>
            <h1 className="text-3xl font-heading font-bold mb-2">Payment Successful!</h1>
            <p className="text-text-secondary mb-6">
              Thank you for subscribing to {paymentDetails?.plan_name || "Premium"}!
            </p>
            
            <div className="glass rounded-xl p-6 mb-8 max-w-md mx-auto">
              <div className="flex items-center justify-between mb-4">
                <span className="text-text-secondary">Plan</span>
                <span className="font-bold">{paymentDetails?.plan_name}</span>
              </div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-text-secondary">Amount</span>
                <span className="font-bold">${paymentDetails?.amount} {paymentDetails?.currency?.toUpperCase()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Status</span>
                <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
                  Active
                </span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                data-testid="explore-features-btn"
                onClick={() => navigate("/characters")}
                className="bg-gradient-to-r from-primary to-accent-purple"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Explore Premium Features
              </Button>
              <Button
                data-testid="view-subscription-btn"
                variant="outline"
                onClick={() => navigate("/profile")}
              >
                View My Subscription
              </Button>
            </div>
          </motion.div>
        );

      case "pending":
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center"
          >
            <div className="w-20 h-20 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-6">
              <Loader2 className="w-10 h-10 text-yellow-500" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Payment Processing</h1>
            <p className="text-text-secondary mb-6">
              Your payment is being processed. This may take a few moments.
            </p>
            <p className="text-sm text-text-muted mb-6">
              You'll receive a confirmation email once the payment is complete.
            </p>
            <Button onClick={() => navigate("/characters")}>
              Continue to App
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </motion.div>
        );

      case "expired":
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center"
          >
            <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-10 h-10 text-red-500" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Session Expired</h1>
            <p className="text-text-secondary mb-6">
              Your payment session has expired. Please try again.
            </p>
            <Button onClick={() => navigate("/subscription")}>
              Back to Plans
            </Button>
          </motion.div>
        );

      case "error":
      default:
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center"
          >
            <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-10 h-10 text-red-500" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Something Went Wrong</h1>
            <p className="text-text-secondary mb-6">
              We couldn't verify your payment. Please contact support if you were charged.
            </p>
            <div className="flex gap-4 justify-center">
              <Button onClick={() => navigate("/subscription")}>
                Try Again
              </Button>
              <Button variant="outline" onClick={() => navigate("/characters")}>
                Go to App
              </Button>
            </div>
          </motion.div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="max-w-lg w-full">
        {renderContent()}
      </div>
    </div>
  );
}
