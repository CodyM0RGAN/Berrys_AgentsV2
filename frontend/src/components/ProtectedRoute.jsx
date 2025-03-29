import { useSelector } from 'react-redux';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

/**
 * Component for protecting routes that require authentication
 * Redirects to login page if user is not authenticated
 * 
 * @returns {JSX.Element} - Outlet for child routes if authenticated, or Navigate to login if not
 */
const ProtectedRoute = () => {
    const { isAuthenticated } = useSelector(state => state.auth);
    const location = useLocation();

    // If not authenticated, redirect to login page with return URL
    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location.pathname }} replace />;
    }

    // If authenticated, render the child routes
    return <Outlet />;
};

export default ProtectedRoute;
