/**
 * Placeholder page component for pages that are not yet implemented
 * 
 * @param {Object} props - Component props
 * @param {string} props.title - Page title
 * @returns {JSX.Element} - Placeholder page
 */
const PlaceholderPage = ({ title }) => {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{title}</h1>
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
                    <p className="text-lg text-gray-600 dark:text-gray-300">
                        This page is under construction.
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                        Coming soon in a future update.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default PlaceholderPage;
