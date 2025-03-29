import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to add the auth token to requests
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Add a response interceptor to handle common errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Handle 401 Unauthorized errors (token expired, etc.)
        if (error.response && error.response.status === 401) {
            // Clear token and redirect to login
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// API endpoints
export const endpoints = {
    // Auth
    login: '/auth/login',
    logout: '/auth/logout',

    // Projects
    projects: '/projects',
    project: (id) => `/projects/${id}`,
    projectAgents: (id) => `/projects/${id}/agents`,
    projectTasks: (id) => `/projects/${id}/tasks`,

    // Agents
    agents: '/agents',
    agent: (id) => `/agents/${id}`,

    // Tasks
    tasks: '/tasks',
    task: (id) => `/tasks/${id}`,

    // Results
    results: '/results',
    result: (id) => `/results/${id}`,

    // Chat
    chatSessions: '/chat/sessions',
    chatSession: (id) => `/chat/sessions/${id}`,
    chatMessage: '/chat/message',

    // Notifications
    notifications: '/notifications',
    notification: (id) => `/notifications/${id}`,
    notificationRead: (id) => `/notifications/${id}/read`,
    notificationsReadAll: '/notifications/read-all',

    // Approvals
    approvals: '/approvals',
    approval: (id) => `/approvals/${id}`,
    approvalApprove: (id) => `/approvals/${id}/approve`,
    approvalReject: (id) => `/approvals/${id}/reject`,

    // System
    systemArchitecture: '/system/architecture',
    systemHealth: '/system/health',
    systemServices: '/system/services',
    systemService: (id) => `/system/services/${id}`,
};

// API methods
export const apiService = {
    // Auth
    login: (credentials) => api.post(endpoints.login, credentials),
    logout: () => api.post(endpoints.logout),

    // Projects
    getProjects: () => api.get(endpoints.projects),
    getProject: (id) => api.get(endpoints.project(id)),
    createProject: (data) => api.post(endpoints.projects, data),
    updateProject: (id, data) => api.put(endpoints.project(id), data),
    deleteProject: (id) => api.delete(endpoints.project(id)),
    getProjectAgents: (id) => api.get(endpoints.projectAgents(id)),
    getProjectTasks: (id) => api.get(endpoints.projectTasks(id)),

    // Agents
    getAgents: () => api.get(endpoints.agents),
    getAgent: (id) => api.get(endpoints.agent(id)),
    createAgent: (data) => api.post(endpoints.agents, data),
    updateAgent: (id, data) => api.put(endpoints.agent(id), data),
    deleteAgent: (id) => api.delete(endpoints.agent(id)),

    // Tasks
    getTasks: () => api.get(endpoints.tasks),
    getTask: (id) => api.get(endpoints.task(id)),
    createTask: (data) => api.post(endpoints.tasks, data),
    updateTask: (id, data) => api.put(endpoints.task(id), data),
    updateTaskStatus: (id, status) => api.patch(endpoints.task(id), { status }),
    deleteTask: (id) => api.delete(endpoints.task(id)),

    // Results
    getResults: () => api.get(endpoints.results),
    getResult: (id) => api.get(endpoints.result(id)),

    // Chat
    getChatSessions: () => api.get(endpoints.chatSessions),
    getChatHistory: (sessionId) => api.get(endpoints.chatSession(sessionId)),
    createChatSession: () => api.post(endpoints.chatSessions),
    sendChatMessage: (sessionId, message) => api.post(endpoints.chatMessage, {
        message,
        session_id: sessionId,
        history: [] // The backend will fetch the history from the session
    }),

    // Notifications
    getNotifications: () => api.get(endpoints.notifications),
    getNotification: (id) => api.get(endpoints.notification(id)),
    markNotificationRead: (id) => api.put(endpoints.notificationRead(id)),
    markAllNotificationsRead: () => api.put(endpoints.notificationsReadAll),
    deleteNotification: (id) => api.delete(endpoints.notification(id)),

    // Approvals
    getApprovals: () => api.get(endpoints.approvals),
    getApproval: (id) => api.get(endpoints.approval(id)),
    approveRequest: (id) => api.put(endpoints.approvalApprove(id)),
    rejectRequest: (id) => api.put(endpoints.approvalReject(id)),

    // System
    getSystemArchitecture: () => api.get(endpoints.systemArchitecture),
    getSystemHealth: () => api.get(endpoints.systemHealth),
    getSystemServices: () => api.get(endpoints.systemServices),
    getSystemService: (id) => api.get(endpoints.systemService(id)),
};

export default apiService;
