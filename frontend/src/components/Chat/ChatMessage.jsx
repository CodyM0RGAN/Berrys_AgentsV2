import { useState } from 'react';

/**
 * Component for rendering a chat message
 * 
 * @param {Object} props - Component props
 * @param {Object} props.message - Message data
 * @param {string} props.message.role - Message role ('user' or 'bot')
 * @param {string} props.message.content - Message content
 * @param {string} props.message.timestamp - Message timestamp
 * @param {Array} props.message.actions - Message actions (optional)
 * @returns {JSX.Element} - Chat message component
 */
const ChatMessage = ({ message }) => {
    const [showActions, setShowActions] = useState(false);

    // Format timestamp
    const formatTime = (timestamp) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Toggle actions visibility
    const toggleActions = () => {
        setShowActions(!showActions);
    };

    // Render message content with basic markdown support
    const renderContent = (content) => {
        // Replace URLs with links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const withLinks = content.replace(urlRegex, (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline">${url}</a>`);

        // Replace ** for bold
        const boldRegex = /\*\*(.*?)\*\*/g;
        const withBold = withLinks.replace(boldRegex, '<strong>$1</strong>');

        // Replace * for italic
        const italicRegex = /\*(.*?)\*/g;
        const withItalic = withBold.replace(italicRegex, '<em>$1</em>');

        // Replace ``` for code blocks
        const codeBlockRegex = /```([\s\S]*?)```/g;
        const withCodeBlocks = withItalic.replace(codeBlockRegex, '<pre class="bg-gray-100 dark:bg-gray-800 p-2 rounded my-2 overflow-x-auto"><code>$1</code></pre>');

        // Replace ` for inline code
        const inlineCodeRegex = /`(.*?)`/g;
        const withInlineCode = withCodeBlocks.replace(inlineCodeRegex, '<code class="bg-gray-100 dark:bg-gray-800 px-1 rounded">$1</code>');

        // Replace new lines with <br>
        const withLineBreaks = withInlineCode.replace(/\n/g, '<br>');

        return <div dangerouslySetInnerHTML={{ __html: withLineBreaks }} />;
    };

    return (
        <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
            <div className={`max-w-[75%] ${message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'} rounded-lg px-4 py-2 shadow`}>
                <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold">
                        {message.role === 'user' ? 'You' : 'Berry'}
                    </span>
                    <span className="text-xs opacity-75">
                        {formatTime(message.timestamp)}
                    </span>
                </div>
                <div className="chat-message-content">
                    {renderContent(message.content)}
                </div>

                {/* Actions (if any) */}
                {message.actions && message.actions.length > 0 && (
                    <div className="mt-2">
                        <button
                            onClick={toggleActions}
                            className="text-xs underline focus:outline-none"
                        >
                            {showActions ? 'Hide actions' : 'Show actions'}
                        </button>

                        {showActions && (
                            <div className="mt-2 space-y-2">
                                {message.actions.map((action, index) => (
                                    <div key={index} className="bg-gray-100 dark:bg-gray-600 p-2 rounded text-sm">
                                        <div className="font-semibold">{action.type}</div>
                                        <div className="text-xs">
                                            <pre className="whitespace-pre-wrap">{JSON.stringify(action.data, null, 2)}</pre>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatMessage;
