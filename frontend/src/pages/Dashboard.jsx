import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import useWebSocket from '../hooks/useWebSocket';
import { fetchAgents } from '../store/slices/agentsSlice';
import { fetchProjects } from '../store/slices/projectsSlice';
import { fetchTasks } from '../store/slices/tasksSlice';
import { handleWebSocketEvent } from '../utils/websocketEvents';

/**
 * Dashboard page component
 * 
 * @returns {JSX.Element} - Dashboard page
 */
const Dashboard = () => {
    // Local state for stats
    const [stats, setStats] = useState({
        activeProjects: 0,
        activeAgents: 0,
        completedTasks: 0,
        pendingTasks: 0
    });

    const dispatch = useDispatch();

    // Get data from Redux store
    const { projects, loading: projectsLoading } = useSelector(state => state.projects);
    const { agents, loading: agentsLoading } = useSelector(state => state.agents);
    const { tasks, loading: tasksLoading } = useSelector(state => state.tasks);

    // Connect to WebSocket and subscribe to events
    const { connected } = useWebSocket('*', handleWebSocketEvent);

    // Fetch data on component mount
    useEffect(() => {
        dispatch(fetchProjects());
        dispatch(fetchAgents());
        dispatch(fetchTasks());
    }, [dispatch]);

    // Update stats when data changes
    useEffect(() => {
        if (projects && agents && tasks) {
            setStats({
                activeProjects: projects.filter(p => p.status === 'active').length,
                activeAgents: agents.filter(a => a.status === 'active').length,
                completedTasks: tasks.filter(t => t.status === 'completed').length,
                pendingTasks: tasks.filter(t => t.status === 'pending').length
            });
        }
    }, [projects, agents, tasks]);

    // Mock recent projects
    const recentProjects = [
        { id: 1, name: 'Website Redesign', status: 'In Progress', progress: 75, agents: 3 },
        { id: 2, name: 'Data Analysis', status: 'In Progress', progress: 45, agents: 2 },
        { id: 3, name: 'Content Creation', status: 'Completed', progress: 100, agents: 5 },
        { id: 4, name: 'Market Research', status: 'Planning', progress: 15, agents: 2 }
    ];

    // Mock active agents
    const activeAgents = [
        { id: 1, name: 'Research Assistant', status: 'Active', tasks: 3, type: 'Research' },
        { id: 2, name: 'Content Writer', status: 'Active', tasks: 2, type: 'Content' },
        { id: 3, name: 'Data Analyst', status: 'Idle', tasks: 0, type: 'Analysis' },
        { id: 4, name: 'Code Generator', status: 'Active', tasks: 1, type: 'Development' }
    ];

    return (
        <div className="container mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-6">Dashboard</h1>

            {/* WebSocket Connection Status */}
            <div className={`mb-4 p-2 rounded-md text-sm ${connected ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'}`}>
                WebSocket: {connected ? 'Connected' : 'Disconnected'}
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900">
                            <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                            </svg>
                        </div>
                        <div className="ml-4">
                            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200">Active Projects</h2>
                            <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                {projectsLoading ? '...' : stats.activeProjects}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-green-100 dark:bg-green-900">
                            <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                            </svg>
                        </div>
                        <div className="ml-4">
                            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200">Active Agents</h2>
                            <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                {agentsLoading ? '...' : stats.activeAgents}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-purple-100 dark:bg-purple-900">
                            <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path>
                            </svg>
                        </div>
                        <div className="ml-4">
                            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200">Completed Tasks</h2>
                            <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                {tasksLoading ? '...' : stats.completedTasks}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-yellow-100 dark:bg-yellow-900">
                            <svg className="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <div className="ml-4">
                            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200">Pending Tasks</h2>
                            <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                {tasksLoading ? '...' : stats.pendingTasks}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Projects */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-8">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Recent Projects</h2>
                </div>
                <div className="p-6">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-700">
                                <tr>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Name</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Progress</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Agents</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {recentProjects.map((project) => (
                                    <tr key={project.id}>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900 dark:text-white">{project.name}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                                ${project.status === 'Completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                                                    project.status === 'In Progress' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                                                        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'}`}>
                                                {project.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                                                <div
                                                    className={`h-2.5 rounded-full ${project.progress === 100 ? 'bg-green-500' :
                                                        project.progress > 50 ? 'bg-blue-500' :
                                                            project.progress > 25 ? 'bg-yellow-500' : 'bg-red-500'
                                                        }`}
                                                    style={{ width: `${project.progress}%` }}
                                                ></div>
                                            </div>
                                            <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">{project.progress}%</span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                            {project.agents} agents
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Active Agents */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Active Agents</h2>
                </div>
                <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {activeAgents.map((agent) => (
                            <div key={agent.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                                <div className="flex items-center mb-2">
                                    <div className={`w-3 h-3 rounded-full mr-2 ${agent.status === 'Active' ? 'bg-green-500' : 'bg-yellow-500'
                                        }`}></div>
                                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">{agent.name}</h3>
                                </div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Type: {agent.type}</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    {agent.tasks} active {agent.tasks === 1 ? 'task' : 'tasks'}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
