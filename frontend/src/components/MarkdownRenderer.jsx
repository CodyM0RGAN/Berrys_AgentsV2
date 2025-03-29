import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeMermaid from 'rehype-mermaid';
import remarkGfm from 'remark-gfm';

/**
 * Component for rendering markdown content with support for Mermaid diagrams
 * 
 * @param {Object} props - Component props
 * @param {string} props.content - Markdown content to render
 * @param {Object} props.options - Additional options for the markdown renderer
 * @returns {JSX.Element} - Rendered markdown content
 */
const MarkdownRenderer = ({ content, options = {} }) => {
    // Configure rehype-mermaid options
    const rehypeMermaidOptions = useMemo(() => ({
        theme: 'default',
        securityLevel: 'loose', // Needed for interactive links
        flowchart: {
            htmlLabels: true,
            curve: 'basis'
        },
    }), []);

    // Custom renderers for markdown elements
    const components = {
        // Add custom styling for headings
        h1: ({ node, children, ...props }) => (
            <h1 className="text-3xl font-bold mt-6 mb-4 dark:text-white" {...props}>
                {children}
            </h1>
        ),
        h2: ({ node, children, ...props }) => (
            <h2 className="text-2xl font-bold mt-5 mb-3 dark:text-white" {...props}>
                {children}
            </h2>
        ),
        h3: ({ node, children, ...props }) => (
            <h3 className="text-xl font-bold mt-4 mb-2 dark:text-white" {...props}>
                {children}
            </h3>
        ),
        // Add custom styling for paragraphs
        p: ({ node, children, ...props }) => (
            <p className="my-3 dark:text-gray-300" {...props}>
                {children}
            </p>
        ),
        // Add custom styling for code blocks
        code: ({ node, inline, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '');

            // Regular code block (Mermaid is handled by rehype-mermaid)
            return !inline ? (
                <pre className={`${className} rounded-md p-4 overflow-auto`}>
                    <code {...props} className={className}>
                        {children}
                    </code>
                </pre>
            ) : (
                <code className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200" {...props}>
                    {children}
                </code>
            );
        },
        // Add custom styling for links
        a: ({ node, children, href, ...props }) => {
            // Handle internal links
            const isInternal = href && !href.startsWith('http');

            if (isInternal) {
                return (
                    <a
                        href={href}
                        className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                        {...props}
                    >
                        {children}
                    </a>
                );
            }

            // External links open in new tab
            return (
                <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                    {...props}
                >
                    {children}
                </a>
            );
        },
        // Add custom styling for lists
        ul: ({ node, children, ...props }) => (
            <ul className="list-disc pl-6 my-3 dark:text-gray-300" {...props}>
                {children}
            </ul>
        ),
        ol: ({ node, children, ...props }) => (
            <ol className="list-decimal pl-6 my-3 dark:text-gray-300" {...props}>
                {children}
            </ol>
        ),
        // Add custom styling for tables
        table: ({ node, children, ...props }) => (
            <div className="overflow-x-auto my-4">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700" {...props}>
                    {children}
                </table>
            </div>
        ),
        thead: ({ node, children, ...props }) => (
            <thead className="bg-gray-50 dark:bg-gray-700" {...props}>
                {children}
            </thead>
        ),
        tbody: ({ node, children, ...props }) => (
            <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700" {...props}>
                {children}
            </tbody>
        ),
        tr: ({ node, children, ...props }) => (
            <tr className="hover:bg-gray-50 dark:hover:bg-gray-700" {...props}>
                {children}
            </tr>
        ),
        th: ({ node, children, ...props }) => (
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-300" {...props}>
                {children}
            </th>
        ),
        td: ({ node, children, ...props }) => (
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300" {...props}>
                {children}
            </td>
        ),
    };

    return (
        <div className="markdown-body prose dark:prose-invert max-w-none">
            <ReactMarkdown
                components={components}
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[[rehypeMermaid, rehypeMermaidOptions]]}
                {...options}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
};

export default MarkdownRenderer;
