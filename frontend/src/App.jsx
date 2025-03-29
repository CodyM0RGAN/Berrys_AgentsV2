import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import './App.css';

// Layout and core components
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Eager loaded pages
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import Register from './pages/Register';

// Lazy loaded pages
const Projects = lazy(() => import('./pages/Projects'));
const ProjectDetail = lazy(() => import('./pages/ProjectDetail'));
const Agents = lazy(() => import('./pages/Agents'));
const AgentDetail = lazy(() => import('./pages/AgentDetail'));
const Tasks = lazy(() => import('./pages/Tasks'));
const TaskDetail = lazy(() => import('./pages/TaskDetail'));
const Results = lazy(() => import('./pages/Results'));
const ResultDetail = lazy(() => import('./pages/ResultDetail'));
const Approvals = lazy(() => import('./pages/Approvals'));
const Notifications = lazy(() => import('./pages/Notifications'));
const Settings = lazy(() => import('./pages/Settings'));
const Profile = lazy(() => import('./pages/Profile'));

// Loading fallback
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
  </div>
);

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          {/* Dashboard */}
          <Route index element={<Dashboard />} />

          {/* Projects */}
          <Route path="projects" element={
            <Suspense fallback={<LoadingFallback />}>
              <Projects />
            </Suspense>
          } />
          <Route path="projects/:id" element={
            <Suspense fallback={<LoadingFallback />}>
              <ProjectDetail />
            </Suspense>
          } />

          {/* Agents */}
          <Route path="agents" element={
            <Suspense fallback={<LoadingFallback />}>
              <Agents />
            </Suspense>
          } />
          <Route path="agents/:id" element={
            <Suspense fallback={<LoadingFallback />}>
              <AgentDetail />
            </Suspense>
          } />

          {/* Tasks */}
          <Route path="tasks" element={
            <Suspense fallback={<LoadingFallback />}>
              <Tasks />
            </Suspense>
          } />
          <Route path="tasks/:id" element={
            <Suspense fallback={<LoadingFallback />}>
              <TaskDetail />
            </Suspense>
          } />

          {/* Results */}
          <Route path="results" element={
            <Suspense fallback={<LoadingFallback />}>
              <Results />
            </Suspense>
          } />
          <Route path="results/:id" element={
            <Suspense fallback={<LoadingFallback />}>
              <ResultDetail />
            </Suspense>
          } />

          {/* Approvals */}
          <Route path="approvals" element={
            <Suspense fallback={<LoadingFallback />}>
              <Approvals />
            </Suspense>
          } />

          {/* Notifications */}
          <Route path="notifications" element={
            <Suspense fallback={<LoadingFallback />}>
              <Notifications />
            </Suspense>
          } />

          {/* User */}
          <Route path="settings" element={
            <Suspense fallback={<LoadingFallback />}>
              <Settings />
            </Suspense>
          } />
          <Route path="profile" element={
            <Suspense fallback={<LoadingFallback />}>
              <Profile />
            </Suspense>
          } />
        </Route>
      </Route>

      {/* 404 route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
