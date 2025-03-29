# Berry's Agents Web Dashboard

This is the frontend for the Berry's Agents V2 platform, providing a modern React-based user interface for managing projects, agents, and tasks.

## Overview

This frontend application is part of the Phase 3 revamp of the Berrys_AgentsV2 project, migrating from a Flask-rendered UI to a modern, modular React frontend. It provides a dynamic, real-time, and highly interactive user experience across project, agent, and task interfaces.

## Features

- Modern React-based UI with Vite for fast development
- Redux Toolkit for state management
- React Router for client-side routing
- Real-time updates via WebSocket integration with Redis event streams
- Markdown rendering with Mermaid diagram support
- Responsive design with Tailwind CSS
- Dark mode support

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── assets/          # Images, fonts, etc.
│   ├── components/      # Reusable UI components
│   │   ├── Layout.jsx   # Main layout component
│   │   ├── Navbar.jsx   # Top navigation bar
│   │   ├── Sidebar.jsx  # Side navigation menu
│   │   └── ...
│   ├── hooks/           # Custom React hooks
│   │   ├── useApi.js    # Hook for API calls
│   │   ├── useWebSocket.js # Hook for WebSocket integration
│   │   └── ...
│   ├── pages/           # Page components
│   │   ├── Dashboard.jsx # Main dashboard page
│   │   └── ...
│   ├── services/        # Service modules
│   │   ├── api.js       # API service
│   │   ├── websocket.js # WebSocket service
│   │   └── ...
│   ├── store/           # Redux store
│   │   ├── index.js     # Store configuration
│   │   ├── slices/      # Redux slices
│   │   │   ├── authSlice.js
│   │   │   ├── projectsSlice.js
│   │   │   ├── agentsSlice.js
│   │   │   ├── tasksSlice.js
│   │   │   └── ...
│   ├── utils/           # Utility functions
│   ├── App.jsx          # Main App component
│   ├── App.css          # Global styles
│   ├── index.css        # Tailwind imports and base styles
│   └── main.jsx         # Entry point
├── .env                 # Environment variables (not in repo)
├── .env.example         # Example environment variables
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── tailwind.config.js   # Tailwind CSS configuration
└── vite.config.js       # Vite configuration
```

## Getting Started

### Prerequisites

- Node.js (v18+)
- npm (v9+)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/berrys-agentsv2.git
   cd berrys-agentsv2
   ```

2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

4. Update the `.env` file with your API and WebSocket URLs:
   ```
   VITE_API_URL=http://localhost:8080/api
   VITE_WS_URL=http://localhost:8080
   ```

### Development

Start the development server:

```bash
npm run dev
```

This will start the Vite development server at [http://localhost:5173](http://localhost:5173).

### Building for Production

Build the application for production:

```bash
npm run build
```

This will create a `dist` directory with the compiled assets.

Preview the production build:

```bash
npm run preview
```

## Key Concepts

### Authentication

Authentication is handled using JWT tokens. The `authSlice.js` manages the authentication state, and the API service automatically includes the token in requests.

### State Management

Redux Toolkit is used for state management. The store is organized into slices for different domains (auth, projects, agents, tasks).

### API Integration

The `apiService` provides methods for interacting with the backend API. It handles authentication, error handling, and request/response formatting.

### Real-time Updates

WebSocket integration is provided through the `websocketService` and `useWebSocket` hook. This enables real-time updates from the backend via Redis event streams.

### Routing

React Router is used for client-side routing. Protected routes require authentication.

### Styling

Tailwind CSS is used for styling. Dark mode is supported through Tailwind's dark mode classes.

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
