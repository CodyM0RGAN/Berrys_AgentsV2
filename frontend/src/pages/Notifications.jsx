import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchNotifications, markAllNotificationsRead, markNotificationRead } from '../store/slices/notificationsSlice';

const Notifications = () => {
    const dispatch = useDispatch();
    const { notifications, loading, error } = useSelector(state => state.notifications);

    useEffect(() => {
        dispatch(fetchNotifications());
    }, [dispatch]);

    const handleMarkAllRead = () => {
        dispatch(markAllNotificationsRead());
    };

    const handleMarkRead = (id) => {
        dispatch(markNotificationRead(id));
    };

    // Group notifications by date
    const groupedNotifications = notifications.reduce((groups, notification) => {
        const date = new Date(notification.createdAt).toLocaleDateString();
        if (!groups[date]) {
            groups[date] = [];
        }
        groups[date].push(notification);
        return groups;
    }, {});

    // Sort dates in descending order (newest first)
    const sortedDates = Object.keys(groupedNotifications).sort((a, b) => {
        return new Date(b) - new Date(a);
    });

    // Check if there are any unread notifications
    const hasUnread = notifications.some(notification => !notification.read);

    return (
        <div className="container mx-auto px-4 py-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Notifications</h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Stay updated with the latest activities and alerts.
                    </p>
                </div>
                {hasUnread && (
                    <button
                        className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 dark:text-blue-400 dark:bg-blue-900/20 dark:hover:bg-blue-900/30"
                        onClick={handleMarkAllRead}
                    >
                        Mark all as read
                    </button>
                )}
            </div>

            {/* Error message */}
            {error && (
                <div className="mb-6 p-4 bg-red-100 border-l-4 border-red-500 text-red-700 dark:bg-red-900/30 dark:text-red-400 dark:border-red-500">
                    <p className="font-medium">Error loading notifications</p>
                    <p>{error}</p>
                </div>
            )}

            {/* Loading state */}
            {loading ? (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-white"></div>
                </div>
            ) : notifications.length > 0 ? (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
                    {sortedDates.map(date => (
                        <div key={date}>
                            <div className="bg-gray-50 dark:bg-gray-700 px-6 py-3">
                                <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300">{date}</h2>
                            </div>
                            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                                {groupedNotifications[date].map(notification => {
                                    // Determine icon and color based on notification type
                                    let iconColor, icon;
                                    switch (notification.type) {
                                        case 'info':
                                            iconColor = 'text-blue-500 dark:text-blue-400';
                                            icon = (
                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"></path>
                                                </svg>
                                            );
                                            break;
                                        case 'success':
                                            iconColor = 'text-green-500 dark:text-green-400';
                                            icon = (
                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
                                                </svg>
                                            );
                                            break;
                                        case 'warning':
                                            iconColor = 'text-yellow-500 dark:text-yellow-400';
                                            icon = (
                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"></path>
                                                </svg>
                                            );
                                            break;
                                        case 'error':
                                            iconColor = 'text-red-500 dark:text-red-400';
                                            icon = (
                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"></path>
                                                </svg>
                                            );
                                            break;
                                        default:
                                            iconColor = 'text-gray-500 dark:text-gray-400';
                                            icon = (
                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"></path>
                                                </svg>
                                            );
                                    }

                                    return (
                                        <li
                                            key={notification.id}
                                            className={`px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${!notification.read ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}
                                            onClick={() => handleMarkRead(notification.id)}
                                        >
                                            <div className="flex items-start">
                                                <div className={`flex-shrink-0 ${iconColor} mt-1 mr-3`}>
                                                    {icon}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className={`text-sm font-medium ${notification.read ? 'text-gray-700 dark:text-gray-300' : 'text-gray-900 dark:text-white'}`}>
                                                        {notification.title}
                                                    </p>
                                                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                                        {notification.message}
                                                    </p>
                                                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                                        {new Date(notification.createdAt).toLocaleTimeString()}
                                                    </p>
                                                </div>
                                                {!notification.read && (
                                                    <span className="flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full ml-2 mt-2"></span>
                                                )}
                                            </div>
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 text-center">
                    <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                    </svg>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">No notifications</h3>
                    <p className="text-gray-500 dark:text-gray-400">You're all caught up! Check back later for new notifications.</p>
                </div>
            )}
        </div>
    );
};

export default Notifications;
