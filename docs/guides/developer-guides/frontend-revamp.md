# Frontend Revamp Developer Guide

## Overview

This document provides an overview of the React-based frontend revamp for the Berry's Agents V2 platform. The revamp migrates the UI from Flask-rendered templates to a modern, modular React frontend with real-time updates and improved user experience.

## Architecture

The frontend architecture follows modern React best practices and is organized into a modular, maintainable structure:

```
frontend/
├── public/              # Static assets
├── src/
│   ├── assets/          # Images, fonts, etc.
│   ├── components/      # Reusable UI components
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   ├── services/        # Service modules
│   ├── store/           # Redux store
│   │   ├── slices/      # Redux slices
│   ├── utils/           # Utility functions
│   ├── App.jsx          # Main App component
│   ├── main.jsx         # Entry point
```

### Key Technologies

- **React**: UI library for building component-based interfaces
- **Redux Toolkit**: State management with simplified Redux setup
- **React Router**: Client-side routing
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Axios**: HTTP client for API requests
- **Socket.IO**: WebSocket client for real-time updates
- **Vite**: Build tool and development server

## Core Concepts

### Routing

The application uses React Router for client-side routing. The main routes are defined in `App.jsx` and include:

- `/`: Dashboard
- `/projects`: Projects list
- `/projects/:id`: Project details
- `/agents`: Agents list
- `/agents/:id`: Agent details
- `/tasks`: Tasks list
- `/tasks/:id`: Task details
- `/results`: Results list
- `/results/:id`: Result details
- `/system`: System architecture and health
- `/settings`: User settings
- `/profile`: User profile
- `/login`: Login page
- `/register`: Registration page

Protected routes require authentication and are wrapped in the `ProtectedRoute` component, which redirects unauthenticated users to the login page.

### State Management

Redux Toolkit is used for state management. The store is organized into slices for different domains:

- `authSlice`: Authentication state (user, token, login/logout)
- `projectsSlice`: Projects state (list, current project, CRUD operations)
- `agentsSlice`: Agents state (list, current agent, CRUD operations)
- `tasksSlice`: Tasks state (list, current task, CRUD operations)
- `chatSlice`: Chat state (messages, sessions, typing status)
- `notificationsSlice`: Notifications state (list, read status)
- `systemSlice`: System state (architecture, health metrics)

Each slice provides:
- Initial state
- Reducers for synchronous state updates
- Async thunks for API calls
- Selectors for accessing state

### API Integration

The `apiService` provides methods for interacting with the backend API. It handles:

- Authentication via JWT tokens
- Request/response formatting
- Error handling
- Automatic token inclusion in requests

### Real-time Updates

WebSocket integration is provided through the `websocketService` and `useWebSocket` hook. This enables real-time updates from the backend via Redis event streams.

The flow is:
1. Backend services publish events to Redis streams
2. WebSocket server listens to Redis streams and forwards events to connected clients
3. Frontend receives events via WebSocket and updates Redux store
4. UI components re-render with updated data

### Custom Hooks

Custom hooks encapsulate reusable logic:

- `useApi`: Simplifies API calls with loading and error states
- `useWebSocket`: Manages WebSocket connections and event subscriptions

## Implementation Details

### Authentication Flow

1. User enters credentials on Login page
2. `login` thunk is dispatched to authenticate with the backend
3. On success, JWT token is stored in localStorage
4. Auth state is updated in Redux
5. User is redirected to the requested page or dashboard

### WebSocket Integration

1. `websocketService` connects to the WebSocket server when the user is authenticated
2. Components use `useWebSocket` hook to subscribe to events
3. When events are received, they are processed by `handleWebSocketEvent` utility
4. Appropriate Redux actions are dispatched to update the store
5. UI components re-render with the updated data

### Lazy Loading

React's `lazy` and `Suspense` are used for code splitting. This improves initial load time by only loading the code needed for the current route.

### Dark Mode

Dark mode is supported through Tailwind CSS's dark mode classes. The theme is toggled based on user preference and stored in localStorage.

### Chat Interface

The chat interface allows users to interact with Berry, a friendly AI assistant that helps users create and manage projects. Key components include:

1. **ChatWindow**: The main chat interface component
   - Displays chat messages
   - Provides input for user messages
   - Shows typing indicators
   - Supports markdown rendering

2. **ChatMessage**: Component for rendering individual chat messages
   - Supports different message types (text, markdown, actions)
   - Shows message status (sent, delivered, read)
   - Displays timestamps

3. **ChatInput**: Component for user message input
   - Text input with send button
   - Attachment support
   - Emoji picker

4. **ChatSlice**: Redux slice for chat state management
   - Stores chat messages and sessions
   - Manages typing status
   - Handles message sending and receiving

The chat interface integrates with the backend through:
- API endpoints for sending messages and retrieving history
- WebSocket for real-time message updates
- Redux for state management

### Notifications & Approvals

The notifications system provides users with updates and approval requests. Key components include:

1. **NotificationsDropdown**: Component for displaying notifications
   - Shows notification list
   - Supports different notification types
   - Provides mark as read functionality

2. **ApprovalRequest**: Component for handling approval workflows
   - Displays approval details
   - Provides approve/reject actions
   - Shows approval status

3. **NotificationsSlice**: Redux slice for notifications state management
   - Stores notifications list
   - Manages read status
   - Handles approval actions

The notifications system integrates with the backend through:
- API endpoints for retrieving and updating notifications
- WebSocket for real-time notification updates
- Redux for state management

### System Architecture Visualization

The system architecture page provides a visual representation of the system components and their relationships. Key features include:

1. **Architecture Diagram**: Visual representation of system components
   - Shows services and their relationships
   - Provides status indicators for each service
   - Supports interactive exploration

2. **Health Monitoring**: Visualizations for system health
   - Charts for performance metrics
   - Alerts for system issues
   - Historical data viewing

3. **SystemSlice**: Redux slice for system state management
   - Stores architecture information
   - Manages health metrics
   - Handles status updates

The system architecture page integrates with the backend through:
- API endpoints for retrieving architecture and health information
- WebSocket for real-time status updates
- Redux for state management

## Development Workflow

### Adding a New Feature

1. Create necessary Redux slice(s) in `store/slices/`
2. Add API methods to `services/api.js`
3. Create UI components in `components/`
4. Create page component(s) in `pages/`
5. Add routes to `App.jsx`
6. Add WebSocket event handlers if needed

### Adding a New Page

1. Create the page component in `pages/`
2. Add the route to `App.jsx`
3. Add navigation link in `Sidebar.jsx` if needed

### Adding Real-time Updates

1. Ensure the backend publishes events to Redis streams
2. Add event handler in `utils/websocketEvents.js`
3. Use `useWebSocket` hook in the component that needs real-time updates

### Adding a New Chat Feature

1. Update the chat components in `components/Chat/`
2. Add new actions to the chat slice in `store/slices/chatSlice.js`
3. Add API methods to `services/api.js` if needed
4. Add WebSocket event handlers for real-time updates

### Adding a New Notification Type

1. Update the notification components in `components/Notifications/`
2. Add new actions to the notifications slice in `store/slices/notificationsSlice.js`
3. Add API methods to `services/api.js` if needed
4. Add WebSocket event handlers for real-time updates

## Testing

The frontend can be tested using:

- Jest for unit tests
- React Testing Library for component tests
- Cypress for end-to-end tests

## Deployment

The frontend is built using Vite's production build process:

```bash
npm run build
```

This creates a `dist` directory with optimized assets that can be served by any static file server.

## Future Improvements

- Add comprehensive test coverage
- Implement error boundary components
- Add performance monitoring
- Implement feature flags for gradual rollout
- Add analytics tracking
- Enhance accessibility features
- Implement offline support
- Add multi-language support
