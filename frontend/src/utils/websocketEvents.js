import { store } from '../store';
import { updateAgent } from '../store/slices/agentsSlice';
import { messageReceived, setTypingStatus } from '../store/slices/chatSlice';
import {
    approvalCompleted,
    approvalCreated,
    approvalUpdated,
    notificationReceived,
    notificationUpdated
} from '../store/slices/notificationsSlice';
import { projectCreated, projectDeleted, updateProject } from '../store/slices/projectsSlice';
import { updateTask } from '../store/slices/tasksSlice';

/**
 * Handle WebSocket events and dispatch appropriate Redux actions
 * 
 * @param {Object} event - WebSocket event object
 * @param {string} event.type - Event type (e.g., 'task.updated', 'project.created')
 * @param {Object} event.data - Event data
 */
export const handleWebSocketEvent = (event) => {
    const { type, data } = event;

    // Extract the category and action from the event type
    const [category, action] = type.split('.');

    // Handle events based on category
    switch (category) {
        case 'task':
            handleTaskEvent(action, data);
            break;
        case 'project':
            handleProjectEvent(action, data);
            break;
        case 'agent':
            handleAgentEvent(action, data);
            break;
        case 'workflow':
            handleWorkflowEvent(action, data);
            break;
        case 'chat':
            handleChatEvent(action, data);
            break;
        case 'notification':
            handleNotificationEvent(action, data);
            break;
        case 'approval':
            handleApprovalEvent(action, data);
            break;
        case 'system':
            handleSystemEvent(action, data);
            break;
        default:
            console.warn(`Unhandled event category: ${category}`);
    }
};

/**
 * Handle notification-related events
 * 
 * @param {string} action - Action type (e.g., 'created', 'updated', 'deleted')
 * @param {Object} data - Notification data
 */
const handleNotificationEvent = (action, data) => {
    switch (action) {
        case 'created':
            // Add the new notification to the Redux store
            store.dispatch(notificationReceived(data));
            break;
        case 'updated':
            // Update notification in Redux store
            store.dispatch(notificationUpdated(data));
            break;
        case 'deleted':
            // Handle notification deleted event
            // This would typically remove the notification from the notifications list
            console.log('Notification deleted:', data);
            break;
        default:
            console.warn(`Unhandled notification action: ${action}`);
    }
};

/**
 * Handle approval-related events
 * 
 * @param {string} action - Action type (e.g., 'created', 'updated', 'completed')
 * @param {Object} data - Approval data
 */
const handleApprovalEvent = (action, data) => {
    switch (action) {
        case 'created':
            // Add the new approval to the Redux store
            store.dispatch(approvalCreated(data));
            break;
        case 'updated':
            // Update approval in Redux store
            store.dispatch(approvalUpdated(data));
            break;
        case 'completed':
            // Mark approval as completed in Redux store
            store.dispatch(approvalCompleted(data));
            break;
        default:
            console.warn(`Unhandled approval action: ${action}`);
    }
};

/**
 * Handle system-related events
 * 
 * @param {string} action - Action type (e.g., 'service_status_changed', 'health_alert')
 * @param {Object} data - System data
 */
const handleSystemEvent = (action, data) => {
    // For now, just log system events
    // These will be handled by the systemSlice when we implement it
    console.log(`System ${action}:`, data);
};

/**
 * Handle task-related events
 * 
 * @param {string} action - Action type (e.g., 'created', 'updated', 'deleted')
 * @param {Object} data - Task data
 */
const handleTaskEvent = (action, data) => {
    switch (action) {
        case 'created':
            // Handle task created event
            // This would typically add the task to the tasks list
            console.log('Task created:', data);
            break;
        case 'updated':
            // Update task in Redux store
            store.dispatch(updateTask({ id: data.id, data }));
            break;
        case 'deleted':
            // Handle task deleted event
            // This would typically remove the task from the tasks list
            console.log('Task deleted:', data);
            break;
        case 'status_changed':
            // Update task status in Redux store
            store.dispatch(updateTask({ id: data.id, data }));
            break;
        default:
            console.warn(`Unhandled task action: ${action}`);
    }
};

/**
 * Handle project-related events
 * 
 * @param {string} action - Action type (e.g., 'created', 'updated', 'deleted')
 * @param {Object} data - Project data
 */
const handleProjectEvent = (action, data) => {
    switch (action) {
        case 'created':
            // Add the new project to the Redux store
            store.dispatch(projectCreated(data));
            break;
        case 'updated':
            // Update project in Redux store
            store.dispatch(updateProject({ id: data.id, data }));
            break;
        case 'deleted':
            // Remove the project from the Redux store
            store.dispatch(projectDeleted(data.id));
            break;
        case 'agent_added':
            // Handle agent added to project event
            console.log('Agent added to project:', data);
            // If we're viewing this project, we might want to refresh the agents list
            if (store.getState().projects.currentProject?.id === data.projectId) {
                // This would typically trigger a re-fetch of the project's agents
                console.log('Refreshing project agents');
            }
            break;
        case 'agent_removed':
            // Handle agent removed from project event
            console.log('Agent removed from project:', data);
            // Similar to agent_added, we might want to refresh the agents list
            if (store.getState().projects.currentProject?.id === data.projectId) {
                console.log('Refreshing project agents');
            }
            break;
        case 'task_added':
            // Handle task added to project event
            console.log('Task added to project:', data);
            // If we're viewing this project, we might want to refresh the tasks list
            if (store.getState().projects.currentProject?.id === data.projectId) {
                console.log('Refreshing project tasks');
            }
            break;
        case 'task_removed':
            // Handle task removed from project event
            console.log('Task removed from project:', data);
            // Similar to task_added, we might want to refresh the tasks list
            if (store.getState().projects.currentProject?.id === data.projectId) {
                console.log('Refreshing project tasks');
            }
            break;
        default:
            console.warn(`Unhandled project action: ${action}`);
    }
};

/**
 * Handle agent-related events
 * 
 * @param {string} action - Action type (e.g., 'created', 'updated', 'deleted')
 * @param {Object} data - Agent data
 */
const handleAgentEvent = (action, data) => {
    switch (action) {
        case 'created':
            // Handle agent created event
            console.log('Agent created:', data);
            break;
        case 'updated':
            // Update agent in Redux store
            store.dispatch(updateAgent({ id: data.id, data }));
            break;
        case 'deleted':
            // Handle agent deleted event
            console.log('Agent deleted:', data);
            break;
        case 'status_changed':
            // Update agent status in Redux store
            store.dispatch(updateAgent({ id: data.id, data }));
            break;
        default:
            console.warn(`Unhandled agent action: ${action}`);
    }
};

/**
 * Handle workflow-related events
 * 
 * @param {string} action - Action type
 * @param {Object} data - Workflow data
 */
const handleWorkflowEvent = (action, data) => {
    // For now, just log workflow events
    console.log(`Workflow ${action}:`, data);
};

/**
 * Handle chat-related events
 * 
 * @param {string} action - Action type (e.g., 'message_received', 'typing_started')
 * @param {Object} data - Chat data
 */
const handleChatEvent = (action, data) => {
    switch (action) {
        case 'message_received':
            // Add the message to the Redux store
            store.dispatch(messageReceived({
                sessionId: data.session_id,
                message: {
                    id: data.id,
                    role: data.role,
                    content: data.content,
                    timestamp: data.timestamp,
                    metadata: data.metadata
                }
            }));
            break;
        case 'typing_started':
            // Set typing status to true
            store.dispatch(setTypingStatus(true));
            break;
        case 'typing_stopped':
            // Set typing status to false
            store.dispatch(setTypingStatus(false));
            break;
        case 'message_read':
            // Handle message read event
            console.log('Message read:', data);
            break;
        default:
            console.warn(`Unhandled chat action: ${action}`);
    }
};
