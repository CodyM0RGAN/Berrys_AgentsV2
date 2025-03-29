import { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import {
    closeNotificationsDropdown,
    fetchNotifications,
    markAllNotificationsRead,
    markNotificationRead,
    toggleNotificationsDropdown
} from '../../store/slices/notificationsSlice';
import NotificationItem from './NotificationItem';

const NotificationsDropdown = () => {
    const dispatch = useDispatch();
    const dropdownRef = useRef(null);
    const { notifications, unreadCount, isDropdownOpen, loading } = useSelector(state => state.notifications);

    // Fetch notifications when component mounts
    useEffect(() => {
        dispatch(fetchNotifications());
    }, [dispatch]);

    // Handle click outside to close dropdown
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                dispatch(closeNotificationsDropdown());
            }
        };

        if (isDropdownOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isDropdownOpen, dispatch]);

    const handleToggleDropdown = () => {
        dispatch(toggleNotificationsDropdown());
    };

    const handleMarkAllRead = () => {
        dispatch(markAllNotificationsRead());
    };

    const handleNotificationClick = (id) => {
        dispatch(markNotificationRead(id));
    };

    return (
        <div className="relative" ref={dropdownRef}>
            {/* Notification Bell Button */}
            <button
                className="p-2 text-gray-500 rounded-lg hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 relative"
                onClick={handleToggleDropdown}
                aria-label="Notifications"
            >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                </svg>

                {/* Unread Badge */}
                {unreadCount > 0 && (
                    <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
                        {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                )}
            </button>

            {/* Dropdown Menu */}
            {isDropdownOpen && (
                <div className="absolute right-0 z-10 mt-2 w-80 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 dark:bg-gray-700 overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white">Notifications</h3>
                        {unreadCount > 0 && (
                            <button
                                className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                onClick={handleMarkAllRead}
                            >
                                Mark all as read
                            </button>
                        )}
                    </div>

                    {/* Notification List */}
                    <div className="max-h-96 overflow-y-auto">
                        {loading ? (
                            <div className="flex justify-center items-center py-4">
                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 dark:border-white"></div>
                            </div>
                        ) : notifications.length > 0 ? (
                            <ul className="divide-y divide-gray-100 dark:divide-gray-600">
                                {notifications.map(notification => (
                                    <NotificationItem
                                        key={notification.id}
                                        notification={notification}
                                        onClick={() => handleNotificationClick(notification.id)}
                                    />
                                ))}
                            </ul>
                        ) : (
                            <div className="py-4 px-4 text-center text-gray-500 dark:text-gray-400">
                                No notifications
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="border-t border-gray-100 dark:border-gray-600">
                        <Link
                            to="/notifications"
                            className="block w-full px-4 py-2 text-sm text-center text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600"
                            onClick={() => dispatch(closeNotificationsDropdown())}
                        >
                            View all notifications
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
};

export default NotificationsDropdown;
