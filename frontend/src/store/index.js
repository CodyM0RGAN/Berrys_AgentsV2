import { configureStore } from '@reduxjs/toolkit';
import agentsReducer from './slices/agentsSlice';
import authReducer from './slices/authSlice';
import chatReducer from './slices/chatSlice';
import notificationsReducer from './slices/notificationsSlice';
import projectsReducer from './slices/projectsSlice';
import tasksReducer from './slices/tasksSlice';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        projects: projectsReducer,
        agents: agentsReducer,
        tasks: tasksReducer,
        chat: chatReducer,
        notifications: notificationsReducer,
    },
    // Enable Redux DevTools in development
    devTools: process.env.NODE_ENV !== 'production',
});

export default store;
