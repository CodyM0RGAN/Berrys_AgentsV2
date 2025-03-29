import { useCallback, useEffect } from 'react';
import { useSelector } from 'react-redux';
import websocketService from '../services/websocket';

/**
 * Custom hook for using WebSocket connections in React components
 * 
 * @param {string} eventType - The event type to listen for (e.g., 'project.created', 'agent.*')
 * @param {function} callback - The callback function to execute when the event is received
 * @returns {object} - An object containing the connection status and methods
 */
const useWebSocket = (eventType, callback) => {
    const { isAuthenticated } = useSelector(state => state.auth);

    // Connect to WebSocket when authenticated
    useEffect(() => {
        if (isAuthenticated) {
            websocketService.connect();
        }

        // Cleanup on unmount
        return () => {
            // Don't disconnect here as other components might be using the connection
            // Just remove the event handler
            if (eventType && callback) {
                websocketService.off(eventType, callback);
            }
        };
    }, [isAuthenticated]);

    // Add event handler when eventType or callback changes
    useEffect(() => {
        if (isAuthenticated && eventType && callback) {
            websocketService.on(eventType, callback);

            // Cleanup when eventType or callback changes
            return () => {
                websocketService.off(eventType, callback);
            };
        }
    }, [isAuthenticated, eventType, callback]);

    // Method to manually disconnect
    const disconnect = useCallback(() => {
        websocketService.disconnect();
    }, []);

    return {
        connected: websocketService.connected,
        disconnect,
    };
};

export default useWebSocket;
