import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useParams } from 'react-router-dom';
import ProjectModal from '../components/Projects/ProjectModal';
import useApi from '../hooks/useApi';
import useWebSocket from '../hooks/useWebSocket';
import apiService from '../services/api';
import { deleteProject, fetchProject } from '../store/slices/projectsSlice';
import { handleWebSocketEvent } from '../utils/websocketEvents';

/**
 * Project detail page component
 * 
 * @returns {JSX.Element} - Project detail page
 */
const ProjectDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const dispatch = useDispatch();

    // Get project from Redux store
    const { currentProject, loading, error } = useSelector(state => state.projects);

    // Local state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [agents, setAgents] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [loadingAgents, setLoadingAgents] = useState(false);
    const [loadingTasks, setLoadingTasks] = useState(false);
    const [agentsError, setAgentsError] = useState(null);
    const [tasksError, setTasksError] = useState(null);

    // API hooks for fetching agents and tasks
    const { execute: fetchAgents } = useApi(apiService.getProjectAgents);
    const { execute: fetchTasks } = useApi(apiService.getProjectTasks);

    // Connect to WebSocket for real-time updates
    useWebSocket('project.*', handleWebSocketEvent);
    useWebSocket('agent.*', handleWebSocketEvent);
    useWebSocket('task.*', handleWebSocketEvent);

    // Fetch project on component mount or when id changes
    useEffect(() => {
        if (id) {
            dispatch(fetchProject(id));
        }
    }, [dispatch, id]);

    // Fetch associated agents and tasks when project is loaded
    useEffect(() => {
        if (currentProject?.id) {
            // Fetch agents
            setLoadingAgents(true);
            fetchAgents(currentProject.id)
                .then(data => {
                    setAgents(data);
                    setAgentsError(null);
                })
                .catch(err => {
                    console.error('Error fetching agents:', err);
                    setAgentsError('Failed to load agents');
                })
                .finally(() => {
                    setLoadingAgents(false);
                });

            // Fetch tasks
            setLoadingTasks(true);
            fetchTasks(currentProject.id)
                .then(data => {
                    setTasks(data);
                    setTasksError(null);
                })
                .catch(err => {
                    console.error('Error fetching tasks:', err);
                    setTasksError('Failed to load tasks');
                })
                .finally(() => {
                    setLoadingTasks(false);
                });
        }
    }, [currentProject, fetchAgents, fetchTasks]);

    // Handle edit button click
    const handleEdit = () => {
        setIsModalOpen(true);
    };

    // Handle delete button click
    const handleDelete = () => {
        if (window.confirm('Are you sure you want to delete this project?')) {
            dispatch(deleteProject(id))
                .then(() => {
                    navigate('/projects');
                })
                .catch(err => {
                    console.error('Error deleting project:', err);
                });
        }
    };

    // Handle modal submission
    const handleModalSubmit = (projectData) => {
        // The updateProject action is dispatched from the modal
        setIsModalOpen(false);
    };

    // Handle modal close
    const handleModalClose = () => {
        setIsModalOpen(false);
    };

    // Render status badge
    const renderStatusBadge = (status) => {
        let bgColor = '';
        switch (status.toLowerCase()) {
            case 'active':
                bgColor = 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
                break;
            case 'planning':
                bgColor = 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
                break;
            case 'completed':
                bgColor = 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
                break;
            case 'paused':
                bgColor = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
                break;
            case 'cancelled':
                bgColor = 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
                break;
            default:
                bgColor = 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
        }
        return (
            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${bgColor}`}>
                {status}
            </span>
        );
    };

    // If loading, show loading indicator
    if (loading) {
        return (
            <div className="container mx-auto px-4 py-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <div className="animate-pulse">
                        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6 mb-6"></div>
                        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-6"></div>
                    </div>
                </div>
            </div>
        );
    }

    // If error, show error message
    if (error) {
        return (
            <div className="container mx-auto px-4 py-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6 dark:bg-red-900 dark:text-red-100 dark:border-red-700" role="alert">
                    <strong className="font-bold">Error: </strong>
                    <span className="block sm:inline">{error}</span>
                </div>
                <button
                    onClick={() => navigate('/projects')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                    Back to Projects
                </button>
            </div>
        );
    }

    // If no project, show not found message
    if (!currentProject) {
        return (
            <div className="container mx-auto px-4 py-6">
                <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative mb-6 dark:bg-yellow-900 dark:text-yellow-100 dark:border-yellow-700" role="alert">
                    <strong className="font-bold">Not Found: </strong>
                    <span className="block sm:inline">Project not found</span>
                </div>
                <button
                    onClick={() => navigate('/projects')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                    Back to Projects
                </button>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800 dark:text-white">{currentProject.name}</h1>
                    <div className="mt-2">
                        {renderStatusBadge(currentProject.status)}
                        <span className="ml-4 text-sm text-gray-500 dark:text-gray-400">
                            Created: {new Date(currentProject.createdAt).toLocaleDateString()}
                        </span>
                        {currentProject.updatedAt && (
                            <span className="ml-4 text-sm text-gray-500 dark:text-gray-400">
                                Updated: {new Date(currentProject.updatedAt).toLocaleDateString()}
                            </span>
                        )}
                    </div>
                </div>
                <div className="mt-4 md:mt-0 flex space-x-3">
                    <button
                        onClick={handleEdit}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        Edit Project
                    </button>
                    <button
                        onClick={handleDelete}
                        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                    >
                        Delete Project
                    </button>
                </div>
            </div>

            {/* Project Details */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-6">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Project Details</h2>
                </div>
                <div className="p-6">
                    {currentProject.description ? (
                        <p className="text-gray-700 dark:text-gray-300 mb-4">{currentProject.description}</p>
                    ) : (
                        <p className="text-gray-500 dark:text-gray-400 italic mb-4">No description provided</p>
                    )}

                    {/* Tags */}
                    {currentProject.tags && currentProject.tags.length > 0 && (
                        <div className="mb-4">
                            <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-2">Tags</h3>
                            <div className="flex flex-wrap gap-2">
                                {currentProject.tags.map((tag, index) => (
                                    <span
                                        key={index}
                                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Additional project metadata could be displayed here */}
                </div>
            </div>

            {/* Associated Agents */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-6">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Associated Agents</h2>
                </div>
                <div className="p-6">
                    {loadingAgents ? (
                        <div className="animate-pulse">
                            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6 mb-2"></div>
                            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                        </div>
                    ) : agentsError ? (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative dark:bg-red-900 dark:text-red-100 dark:border-red-700" role="alert">
                            <span className="block sm:inline">{agentsError}</span>
                        </div>
                    ) : agents.length === 0 ? (
                        <p className="text-gray-500 dark:text-gray-400 italic">No agents associated with this project</p>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {agents.map(agent => (
                                <div key={agent.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                                    <div className="flex items-center mb-2">
                                        <div className={`w-3 h-3 rounded-full mr-2 ${agent.status === 'active' ? 'bg-green-500' :
                                                agent.status === 'idle' ? 'bg-yellow-500' : 'bg-gray-500'
                                            }`}></div>
                                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                                            <a href={`/agents/${agent.id}`} className="hover:text-blue-600 dark:hover:text-blue-400">
                                                {agent.name}
                                            </a>
                                        </h3>
                                    </div>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Type: {agent.type || 'N/A'}</p>
                                    {agent.description && (
                                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2 truncate">{agent.description}</p>
                                    )}
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        Tasks: {agent.taskCount || 0}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Associated Tasks */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Project Tasks</h2>
                </div>
                <div className="p-6">
                    {loadingTasks ? (
                        <div className="animate-pulse">
                            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6 mb-2"></div>
                            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                        </div>
                    ) : tasksError ? (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative dark:bg-red-900 dark:text-red-100 dark:border-red-700" role="alert">
                            <span className="block sm:inline">{tasksError}</span>
                        </div>
                    ) : tasks.length === 0 ? (
                        <p className="text-gray-500 dark:text-gray-400 italic">No tasks in this project</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-700">
                                    <tr>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                            Task
                                        </th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                            Status
                                        </th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                            Assigned To
                                        </th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                            Created
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                    {tasks.map(task => (
                                        <tr key={task.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="text-sm font-medium text-gray-900 dark:text-white">
                                                    <a href={`/tasks/${task.id}`} className="hover:text-blue-600 dark:hover:text-blue-400">
                                                        {task.name}
                                                    </a>
                                                </div>
                                                {task.description && (
                                                    <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                                                        {task.description}
                                                    </div>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${task.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                                                        task.status === 'in_progress' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                                                            task.status === 'pending' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                                                                'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                                                    }`}>
                                                    {task.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                {task.assignedTo ? (
                                                    <a href={`/agents/${task.assignedTo.id}`} className="hover:text-blue-600 dark:hover:text-blue-400">
                                                        {task.assignedTo.name}
                                                    </a>
                                                ) : (
                                                    'Unassigned'
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                {new Date(task.createdAt).toLocaleDateString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Project Modal */}
            {isModalOpen && (
                <ProjectModal
                    project={currentProject}
                    onSubmit={handleModalSubmit}
                    onClose={handleModalClose}
                />
            )}
        </div>
    );
};

export default ProjectDetail;
