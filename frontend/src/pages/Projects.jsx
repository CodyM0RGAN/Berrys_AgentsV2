import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import ProjectModal from '../components/Projects/ProjectModal';
import useWebSocket from '../hooks/useWebSocket';
import { createProject, deleteProject, fetchProjects, updateProject } from '../store/slices/projectsSlice';
import { handleWebSocketEvent } from '../utils/websocketEvents';

/**
 * Projects page component
 * 
 * @returns {JSX.Element} - Projects page
 */
const Projects = () => {
    const dispatch = useDispatch();
    const { projects, loading, error } = useSelector(state => state.projects);

    // Local state
    const [filteredProjects, setFilteredProjects] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [sortField, setSortField] = useState('name');
    const [sortDirection, setSortDirection] = useState('asc');
    const [currentPage, setCurrentPage] = useState(1);
    const [projectsPerPage] = useState(10);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentProject, setCurrentProject] = useState(null);

    // Connect to WebSocket for real-time updates
    useWebSocket('project.*', handleWebSocketEvent);

    // Fetch projects on component mount
    useEffect(() => {
        dispatch(fetchProjects());
    }, [dispatch]);

    // Filter and sort projects when projects, searchTerm, statusFilter, sortField, or sortDirection changes
    useEffect(() => {
        if (!projects) return;

        let result = [...projects];

        // Apply search filter
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            result = result.filter(project =>
                project.name.toLowerCase().includes(term) ||
                (project.description && project.description.toLowerCase().includes(term))
            );
        }

        // Apply status filter
        if (statusFilter !== 'all') {
            result = result.filter(project => project.status.toLowerCase() === statusFilter.toLowerCase());
        }

        // Apply sorting
        result.sort((a, b) => {
            let aValue = a[sortField];
            let bValue = b[sortField];

            // Handle string comparison
            if (typeof aValue === 'string') {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }

            // Handle date comparison
            if (sortField === 'createdAt' || sortField === 'updatedAt') {
                aValue = new Date(aValue).getTime();
                bValue = new Date(bValue).getTime();
            }

            if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
            if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        setFilteredProjects(result);
    }, [projects, searchTerm, statusFilter, sortField, sortDirection]);

    // Handle sort change
    const handleSort = (field) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('asc');
        }
    };

    // Get current projects for pagination
    const indexOfLastProject = currentPage * projectsPerPage;
    const indexOfFirstProject = indexOfLastProject - projectsPerPage;
    const currentProjects = filteredProjects.slice(indexOfFirstProject, indexOfLastProject);
    const totalPages = Math.ceil(filteredProjects.length / projectsPerPage);

    // Change page
    const paginate = (pageNumber) => setCurrentPage(pageNumber);

    // Open modal for creating a new project
    const handleCreateProject = () => {
        setCurrentProject(null);
        setIsModalOpen(true);
    };

    // Open modal for editing an existing project
    const handleEditProject = (project) => {
        setCurrentProject(project);
        setIsModalOpen(true);
    };

    // Handle project deletion
    const handleDeleteProject = (id) => {
        if (window.confirm('Are you sure you want to delete this project?')) {
            dispatch(deleteProject(id));
        }
    };

    // Handle modal submission
    const handleModalSubmit = (projectData) => {
        if (currentProject) {
            // Update existing project
            dispatch(updateProject({ id: currentProject.id, data: projectData }));
        } else {
            // Create new project
            dispatch(createProject(projectData));
        }
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
            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${bgColor}`}>
                {status}
            </span>
        );
    };

    return (
        <div className="container mx-auto px-4 py-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Projects</h1>
                <button
                    onClick={handleCreateProject}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                    Create Project
                </button>
            </div>

            {/* Filters and Search */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Search
                        </label>
                        <input
                            type="text"
                            id="search"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Search projects..."
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        />
                    </div>
                    <div className="w-full md:w-48">
                        <label htmlFor="status" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Status
                        </label>
                        <select
                            id="status"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        >
                            <option value="all">All Statuses</option>
                            <option value="active">Active</option>
                            <option value="planning">Planning</option>
                            <option value="completed">Completed</option>
                            <option value="paused">Paused</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6 dark:bg-red-900 dark:text-red-100 dark:border-red-700" role="alert">
                    <strong className="font-bold">Error: </strong>
                    <span className="block sm:inline">{error}</span>
                </div>
            )}

            {/* Projects Table */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden mb-6">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                            <tr>
                                <th
                                    scope="col"
                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
                                    onClick={() => handleSort('name')}
                                >
                                    <div className="flex items-center">
                                        Name
                                        {sortField === 'name' && (
                                            <span className="ml-1">
                                                {sortDirection === 'asc' ? '↑' : '↓'}
                                            </span>
                                        )}
                                    </div>
                                </th>
                                <th
                                    scope="col"
                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
                                    onClick={() => handleSort('status')}
                                >
                                    <div className="flex items-center">
                                        Status
                                        {sortField === 'status' && (
                                            <span className="ml-1">
                                                {sortDirection === 'asc' ? '↑' : '↓'}
                                            </span>
                                        )}
                                    </div>
                                </th>
                                <th
                                    scope="col"
                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
                                    onClick={() => handleSort('createdAt')}
                                >
                                    <div className="flex items-center">
                                        Created
                                        {sortField === 'createdAt' && (
                                            <span className="ml-1">
                                                {sortDirection === 'asc' ? '↑' : '↓'}
                                            </span>
                                        )}
                                    </div>
                                </th>
                                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                            {loading ? (
                                <tr>
                                    <td colSpan="4" className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                                        Loading projects...
                                    </td>
                                </tr>
                            ) : currentProjects.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                                        No projects found.
                                    </td>
                                </tr>
                            ) : (
                                currentProjects.map((project) => (
                                    <tr key={project.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                                                <a href={`/projects/${project.id}`} className="hover:text-blue-600 dark:hover:text-blue-400">
                                                    {project.name}
                                                </a>
                                            </div>
                                            {project.description && (
                                                <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                                                    {project.description}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {renderStatusBadge(project.status)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                            {new Date(project.createdAt).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button
                                                onClick={() => handleEditProject(project)}
                                                className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-4"
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => handleDeleteProject(project.id)}
                                                className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Pagination */}
            {filteredProjects.length > projectsPerPage && (
                <div className="flex justify-center">
                    <nav className="inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                        <button
                            onClick={() => paginate(Math.max(1, currentPage - 1))}
                            disabled={currentPage === 1}
                            className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${currentPage === 1
                                    ? 'text-gray-300 cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-gray-500'
                                    : 'text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                                }`}
                        >
                            Previous
                        </button>
                        {[...Array(totalPages).keys()].map(number => (
                            <button
                                key={number + 1}
                                onClick={() => paginate(number + 1)}
                                className={`relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium ${currentPage === number + 1
                                        ? 'z-10 bg-blue-50 border-blue-500 text-blue-600 dark:bg-blue-900 dark:border-blue-500 dark:text-blue-200'
                                        : 'text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                                    }`}
                            >
                                {number + 1}
                            </button>
                        ))}
                        <button
                            onClick={() => paginate(Math.min(totalPages, currentPage + 1))}
                            disabled={currentPage === totalPages}
                            className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${currentPage === totalPages
                                    ? 'text-gray-300 cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-gray-500'
                                    : 'text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                                }`}
                        >
                            Next
                        </button>
                    </nav>
                </div>
            )}

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

export default Projects;
