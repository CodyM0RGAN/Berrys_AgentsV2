import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import useWebSocket from '../../hooks/useWebSocket';
import { createChatSession, fetchChatHistory, fetchChatSessions, sendChatMessage, toggleChat } from '../../store/slices/chatSlice';
import { handleWebSocketEvent } from '../../utils/websocketEvents';
import './Chat.css';
import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';

/**
 * Chat window component
 * 
 * @returns {JSX.Element} - Chat window component
 */
const ChatWindow = () => {
    const dispatch = useDispatch();
    const messagesEndRef = useRef(null);

    // Get chat state from Redux store
    const { currentSession, messages, sessions, loading, isTyping, isChatOpen } = useSelector(state => state.chat);
    const { isAuthenticated } = useSelector(state => state.auth);

    // Local state
    const [initialized, setInitialized] = useState(false);

    // Connect to WebSocket for real-time updates
    useWebSocket('chat.*', handleWebSocketEvent);

    // Initialize chat when authenticated
    useEffect(() => {
        if (isAuthenticated && !initialized) {
            dispatch(fetchChatSessions())
                .then((action) => {
                    if (action.payload && action.payload.length > 0) {
                        // If there are existing sessions, fetch history for the current one
                        const sessionId = action.payload[0].id;
                        dispatch(fetchChatHistory(sessionId));
                    } else {
                        // If no sessions, create a new one
                        dispatch(createChatSession());
                    }
                    setInitialized(true);
                });
        }
    }, [dispatch, isAuthenticated, initialized]);

    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, currentSession]);

    // Handle sending a message
    const handleSendMessage = (message) => {
        if (currentSession) {
            dispatch(sendChatMessage({
                sessionId: currentSession,
                message
            }));
        }
    };

    // Toggle chat window
    const handleToggleChat = () => {
        dispatch(toggleChat());
    };

    // Get current messages
    const currentMessages = currentSession ? messages[currentSession] || [] : [];

    // Render chat button when closed
    if (!isChatOpen) {
        return (
            <button
                onClick={handleToggleChat}
                className="fixed bottom-4 right-4 bg-blue-600 text-white rounded-full p-4 shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 z-50"
                aria-label="Open chat"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                </svg>
            </button>
        );
    }

    return (
        <div className="fixed bottom-4 right-4 w-96 h-[500px] bg-white dark:bg-gray-800 rounded-lg shadow-xl flex flex-col z-50 border border-gray-200 dark:border-gray-700">
            {/* Chat header */}
            <div className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Chat with Berry</h3>
                <div className="flex space-x-2">
                    {isTyping && (
                        <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                            <span className="ml-2">Typing...</span>
                        </div>
                    )}
                    <button
                        onClick={handleToggleChat}
                        className="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-gray-100 focus:outline-none"
                        aria-label="Close chat"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-5 w-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                    </button>
                </div>
            </div>

            {/* Chat messages */}
            <div className="flex-grow overflow-y-auto p-4">
                {loading && currentMessages.length === 0 ? (
                    <div className="flex justify-center items-center h-full">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                    </div>
                ) : currentMessages.length === 0 ? (
                    <div className="flex flex-col justify-center items-center h-full text-gray-500 dark:text-gray-400">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-12 w-12 mb-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={1}
                                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                            />
                        </svg>
                        <p className="text-center">
                            Hi there! I'm Berry, your friendly project assistant. How can I help you today?
                        </p>
                    </div>
                ) : (
                    <>
                        {currentMessages.map((message, index) => (
                            <ChatMessage key={index} message={message} />
                        ))}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            {/* Chat input */}
            <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
        </div>
    );
};

export default ChatWindow;
