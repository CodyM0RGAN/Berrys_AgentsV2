import { Link } from 'react-router-dom';

/**
 * NotFound page component for 404 errors
 * 
 * @returns {JSX.Element} - NotFound page
 */
const NotFound = () => {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full text-center">
                <h1 className="text-9xl font-extrabold text-blue-600 dark:text-blue-400">404</h1>
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white mt-4">Page Not Found</h2>
                <p className="text-lg text-gray-600 dark:text-gray-300 mt-4">
                    The page you are looking for doesn't exist or has been moved.
                </p>
                <div className="mt-8">
                    <Link
                        to="/"
                        className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                    >
                        Go back home
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default NotFound;
