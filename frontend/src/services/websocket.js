import { io } from 'socket.io-client';

class WebSocketService {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.eventHandlers = new Map();
    }

    // Connect to the WebSocket server
    connect() {
        if (this.socket) {
            return;
        }

        const token = localStorage.getItem('token');
        if (!token) {
            console.error('No authentication token found');
            return;
        }

        // Connect to the WebSocket server with authentication
        this.socket = io(import.meta.env.VITE_WS_URL || 'http://localhost:8080', {
            auth: {
                token,
            },
            transports: ['websocket'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
        });

        // Set up event listeners
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.connected = true;

            // Subscribe to event categories
            this.subscribeToEvents();
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.connected = false;
        });

        this.socket.on('error', (error) => {
            console.error('WebSocket error:', error);
        });

        // Listen for events from the server
        this.socket.on('event', (event) => {
            this.handleEvent(event);
        });
    }

    // Disconnect from the WebSocket server
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
        }
    }

    // Subscribe to event categories
    subscribeToEvents() {
        if (!this.socket || !this.connected) {
            return;
        }

        // Subscribe to event categories
        const categories = [
            'project.*',
            'agent.*',
            'task.*',
            'workflow.*',
        ];

        this.socket.emit('subscribe', { categories });
    }

    // Handle incoming events
    handleEvent(event) {
        console.log('Received event:', event);

        // Extract event type and category
        const { type } = event;
        const category = type.split('.')[0];

        // Call handlers for this event type
        if (this.eventHandlers.has(type)) {
            const handlers = this.eventHandlers.get(type);
            handlers.forEach(handler => handler(event));
        }

        // Call handlers for the category wildcard
        const wildcardType = `${category}.*`;
        if (this.eventHandlers.has(wildcardType)) {
            const handlers = this.eventHandlers.get(wildcardType);
            handlers.forEach(handler => handler(event));
        }
    }

    // Add an event handler
    on(eventType, handler) {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, []);
        }

        this.eventHandlers.get(eventType).push(handler);
    }

    // Remove an event handler
    off(eventType, handler) {
        if (!this.eventHandlers.has(eventType)) {
            return;
        }

        const handlers = this.eventHandlers.get(eventType);
        const index = handlers.indexOf(handler);

        if (index !== -1) {
            handlers.splice(index, 1);
        }
    }
}

// Create a singleton instance
const websocketService = new WebSocketService();

export default websocketService;
