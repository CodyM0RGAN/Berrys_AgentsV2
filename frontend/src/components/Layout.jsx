import { Outlet } from 'react-router-dom';
import ChatWindow from './Chat/ChatWindow';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

const Layout = () => {
    return (
        <div className="flex h-screen w-full overflow-hidden bg-gray-100 dark:bg-gray-900">
            {/* Sidebar */}
            <Sidebar />

            {/* Main Content */}
            <div className="flex flex-1 flex-col overflow-hidden">
                {/* Navbar */}
                <Navbar />

                {/* Main Content Area */}
                <main className="flex-1 overflow-auto p-4">
                    <Outlet />
                </main>
            </div>

            {/* Chat Window */}
            <ChatWindow />
        </div>
    );
};

export default Layout;
