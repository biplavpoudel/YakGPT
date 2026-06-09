// frontend/core/event.js

/* EVENT BUS (UI state communication layer) */

export const EventBus = {
  listeners: {},

  on(event, fn) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(fn);
  },

  emit(event, data) {
    const handlers = this.listeners[event];
    if (!handlers || handlers.length === 0) {
      console.warn(`[EventBus] No listeners for event: ${event}`);
      return;
    }
    handlers.forEach(fn => {
      try {
        fn(data);
      } catch (err) {
        console.error(`[EventBus] Handler error in event: ${event}`, err);
      }
    });
  },

  clear() {
    this.listeners = {};
  },

  off(event, fn) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(h => h !== fn);
  }
};