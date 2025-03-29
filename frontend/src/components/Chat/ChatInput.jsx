import { useState } from 'react';

/**
 * Component for chat input field
 * 
 * @param {Object} props - Component props
 * @param {Function} props.onSendMessage - Function to call when message is sent
 * @param {boolean} props.disabled - Whether the input is disabled
 * @returns {JSX.Element} - Chat input component
 */
const ChatInput = ({ onSendMessage, disabled = false }) => {
    const [message, setMessage] = useState('');

    // Handle input change
    const handleChange = (e) => {
        setMessage(e.target.value);
    };

    // Handle key press (Enter to send)
    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Handle send button click
    const handleSend = () => {
        if (message.trim() && !disabled) {
            onSendMessage(message);
            setMessage('');
        }
    };

    return (
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-end">
                <div className="flex-grow">
                    <textarea
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white resize-none"
                        placeholder="Type a message..."
                        rows="2"
                        value={message}
                        onChange={handleChange}
                        onKeyPress={handleKeyPress}
                        disabled={disabled}
                    />
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Press Enter to send, Shift+Enter for new line
                    </div>
                </div>
                <button
                    className={`ml-3 px-4 py-2 rounded-md ${message.trim() && !disabled
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-gray-300 text-gray-500 dark:bg-gray-700 dark:text-gray-400 cursor-not-allowed'
                        } focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`}
                    onClick={handleSend}
                    disabled={!message.trim() || disabled}
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                    >
                        <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z"
                            clipRule="evenodd"
                        />
                    </svg>
                </button>
            </div>
        </div>
    );
};

export default ChatInput;
