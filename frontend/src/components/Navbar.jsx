import { useState } from 'react';
import { Link } from 'react-router-dom';
import NotificationsDropdown from './Notifications/NotificationsDropdown';

const Navbar = () => {
    const [userMenuOpen, setUserMenuOpen] = useState(false);

    // Mock user data - would come from auth context/redux in real app
    const user = {
        name: 'John Doe',
        email: 'john.doe@example.com',
        avatar: 'https://via.placeholder.com/40'
    };

    return (
        <nav className="border-b border-gray-200 bg-white px-4 py-2.5 dark:border-gray-700 dark:bg-gray-800">
            <div className="flex flex-wrap items-center justify-between">
                {/* Logo/Brand - only visible on mobile when sidebar is hidden */}
                <div className="flex items-center md:hidden">
                    <Link to="/" className="flex items-center">
                        <span className="self-center text-xl font-semibold whitespace-nowrap dark:text-white">
                            Berry's Agents
                        </span>
                    </Link>
                </div>

                {/* Search Bar */}
                <div className="flex-1 max-w-lg mx-4 hidden md:block">
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                            <svg className="w-5 h-5 text-gray-500 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd"></path>
                            </svg>
                        </div>
                        <input
                            type="text"
                            className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                            placeholder="Search projects, agents, tasks..."
                        />
                    </div>
                </div>

                {/* Right side items */}
                <div className="flex items-center">
                    {/* Notifications Dropdown */}
                    <NotificationsDropdown />

                    {/* User Menu */}
                    <div className="relative ml-3">
                        <button
                            type="button"
                            className="flex rounded-full bg-gray-800 text-sm focus:ring-4 focus:ring-gray-300 dark:focus:ring-gray-600"
                            onClick={() => setUserMenuOpen(!userMenuOpen)}
                        >
                            <img className="h-8 w-8 rounded-full" src={user.avatar} alt="user" />
                        </button>

                        {/* Dropdown menu */}
                        {userMenuOpen && (
                            <div className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 dark:bg-gray-700">
                                <div className="px-4 py-3">
                                    <span className="block text-sm text-gray-900 dark:text-white">{user.name}</span>
                                    <span className="block text-sm text-gray-500 truncate dark:text-gray-400">{user.email}</span>
                                </div>
                                <hr className="border-gray-200 dark:border-gray-600" />
                                <Link to="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600">Profile</Link>
                                <Link to="/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600">Settings</Link>
                                <hr className="border-gray-200 dark:border-gray-600" />
                                <button className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600">
                                    Sign out
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
