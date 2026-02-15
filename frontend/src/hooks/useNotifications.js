import { useState, useEffect, useCallback } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function useNotifications(user, token) {
  const [permission, setPermission] = useState('default');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(false);

  // Check notification permission on mount
  useEffect(() => {
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  // Register service worker
  const registerServiceWorker = useCallback(async () => {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', registration);
        return registration;
      } catch (error) {
        console.error('Service Worker registration failed:', error);
        return null;
      }
    }
    return null;
  }, []);

  // Request notification permission
  const requestPermission = useCallback(async () => {
    if (!('Notification' in window)) {
      console.log('Notifications not supported');
      return false;
    }

    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      return result === 'granted';
    } catch (error) {
      console.error('Permission request failed:', error);
      return false;
    }
  }, []);

  // Subscribe to push notifications
  const subscribe = useCallback(async () => {
    if (!token || !user) {
      console.log('No user/token for subscription');
      return false;
    }

    setLoading(true);
    try {
      // Request permission first
      const granted = await requestPermission();
      if (!granted) {
        setLoading(false);
        return false;
      }

      // Register service worker
      const registration = await registerServiceWorker();
      if (!registration) {
        setLoading(false);
        return false;
      }

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready;

      // Get VAPID public key
      let vapidKey;
      try {
        const keyRes = await fetch(`${API}/push/vapid-public-key`);
        const keyData = await keyRes.json();
        vapidKey = keyData.publicKey;
      } catch (e) {
        // Use a fallback for demo
        vapidKey = null;
      }

      // Subscribe to push
      const pushSubscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: vapidKey ? urlBase64ToUint8Array(vapidKey) : undefined
      });

      // Send subscription to backend
      const subJson = pushSubscription.toJSON();
      await fetch(`${API}/push/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          endpoint: subJson.endpoint,
          keys: subJson.keys || {}
        })
      });

      setSubscription(pushSubscription);
      setIsSubscribed(true);
      setLoading(false);
      return true;
    } catch (error) {
      console.error('Subscription failed:', error);
      setLoading(false);
      return false;
    }
  }, [token, user, requestPermission, registerServiceWorker]);

  // Unsubscribe from push notifications
  const unsubscribe = useCallback(async () => {
    if (!token) return false;

    setLoading(true);
    try {
      if (subscription) {
        await subscription.unsubscribe();
      }

      await fetch(`${API}/push/unsubscribe`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setSubscription(null);
      setIsSubscribed(false);
      setLoading(false);
      return true;
    } catch (error) {
      console.error('Unsubscribe failed:', error);
      setLoading(false);
      return false;
    }
  }, [token, subscription]);

  // Update user activity (call periodically)
  const updateActivity = useCallback(async () => {
    if (!token) return;

    try {
      await fetch(`${API}/push/update-activity`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    } catch (error) {
      // Silent fail
    }
  }, [token]);

  // Show a local notification (for testing/demo)
  const showLocalNotification = useCallback(async (title, body, icon, url) => {
    if (permission !== 'granted') {
      const granted = await requestPermission();
      if (!granted) return;
    }

    const registration = await navigator.serviceWorker.ready;
    
    registration.showNotification(title, {
      body,
      icon: icon || '/logo192.png',
      badge: '/logo192.png',
      tag: 'local-notification',
      vibrate: [100, 50, 100],
      data: { url: url || '/characters' },
      actions: [
        { action: 'chat', title: 'Chat Now 💬' },
        { action: 'later', title: 'Later' }
      ]
    });
  }, [permission, requestPermission]);

  // Check existing subscription on mount
  useEffect(() => {
    const checkSubscription = async () => {
      if ('serviceWorker' in navigator && 'PushManager' in window) {
        try {
          const registration = await navigator.serviceWorker.ready;
          const sub = await registration.pushManager.getSubscription();
          if (sub) {
            setSubscription(sub);
            setIsSubscribed(true);
          }
        } catch (error) {
          console.error('Error checking subscription:', error);
        }
      }
    };

    checkSubscription();
  }, []);

  // Update activity periodically
  useEffect(() => {
    if (!token) return;

    // Update immediately
    updateActivity();

    // Update every 5 minutes
    const interval = setInterval(updateActivity, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [token, updateActivity]);

  return {
    permission,
    isSubscribed,
    loading,
    subscribe,
    unsubscribe,
    requestPermission,
    updateActivity,
    showLocalNotification,
    isSupported: 'Notification' in window && 'serviceWorker' in navigator
  };
}

// Helper function to convert VAPID key
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export default useNotifications;
