import React, { useEffect } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { NotificationProvider } from './contexts/NotificationContext.js';
import { useAuth } from './contexts/AuthContext.js';
import MainLayout from './layouts/MainLayout.js';
import Dashboard from './pages/Dashboard.tsx';
import Login from './pages/Login.tsx';
import Profile from './pages/Profile.tsx';
import Preferences from './pages/Preferences.tsx';
import NotFound from './pages/NotFound.tsx';
import Unauthorized from './pages/Unauthorized.tsx';
import ProtectedRoute from './components/ProtectedRoute.js';

const App = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Handle redirect after successful authentication
  useEffect(() => {
    if (isAuthenticated && location.pathname === '/login') {
      // Check for stored redirect path
      const redirectPath = localStorage.getItem('auth_redirect') || '/';
      localStorage.removeItem('auth_redirect');
      navigate(redirectPath, { replace: true });
    }
  }, [isAuthenticated, navigate, location.pathname]);
  
  return (
    <NotificationProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/unauthorized" element={<Unauthorized />} />
        <Route path="/" element={
          <ProtectedRoute>
            <MainLayout>
              <Dashboard />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute>
            <MainLayout>
              <Profile />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/preferences" element={
          <ProtectedRoute>
            <MainLayout>
              <Preferences />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </NotificationProvider>
  );
};

export default App;