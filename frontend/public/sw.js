// Service Worker for Push Notifications
// This file handles background push notifications from AI characters

const CACHE_NAME = 'ai-companion-v1';

// Install event
self.addEventListener('install', (event) => {
  console.log('Service Worker installed');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker activated');
  event.waitUntil(clients.claim());
});

// Push notification event
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event);
  
  let data = {
    title: 'AI Companion',
    body: 'Someone is thinking about you...',
    icon: '/logo192.png',
    badge: '/logo192.png',
    tag: 'ai-companion',
    data: { url: '/characters' }
  };
  
  try {
    if (event.data) {
      const payload = event.data.json();
      data = {
        title: payload.title || data.title,
        body: payload.body || data.body,
        icon: payload.icon || data.icon,
        badge: payload.badge || data.badge,
        tag: payload.tag || data.tag,
        data: payload.data || data.data,
        image: payload.image,
        vibrate: [100, 50, 100],
        requireInteraction: true,
        actions: [
          { action: 'chat', title: 'Chat Now 💬' },
          { action: 'later', title: 'Later' }
        ]
      };
    }
  } catch (e) {
    console.error('Error parsing push data:', e);
  }
  
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      badge: data.badge,
      tag: data.tag,
      data: data.data,
      image: data.image,
      vibrate: data.vibrate,
      requireInteraction: data.requireInteraction,
      actions: data.actions
    })
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  const action = event.action;
  const notificationData = event.notification.data || {};
  
  if (action === 'later') {
    // User clicked "Later", just close
    return;
  }
  
  // Default action or "Chat Now" clicked
  const urlToOpen = notificationData.url || '/characters';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Check if there's already a window open
        for (const client of windowClients) {
          if (client.url.includes(self.location.origin)) {
            // Focus existing window and navigate
            return client.focus().then(() => {
              return client.navigate(urlToOpen);
            });
          }
        }
        // No existing window, open new one
        return clients.openWindow(urlToOpen);
      })
  );
});

// Notification close event
self.addEventListener('notificationclose', (event) => {
  console.log('Notification closed:', event);
});

// Background sync for offline notifications
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-notifications') {
    console.log('Background sync triggered');
  }
});

// Periodic background sync for checking notifications
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'check-notifications') {
    event.waitUntil(checkForNotifications());
  }
});

async function checkForNotifications() {
  // This would be called periodically to check for new notifications
  console.log('Checking for new notifications...');
}
