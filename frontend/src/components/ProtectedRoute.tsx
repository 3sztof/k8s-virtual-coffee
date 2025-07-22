import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spinner, Box } from '@cloudscape-design/components';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireAdmin = false 
}) => {
  const { user, loading } = useAuth();
  const location = useLocation();
  
  // Show loading state while checking authentication
  if (loading) {
    return (
      <Box
        margin="xxl"
        textAlign="center"
        color="inherit"
      >
        <Spinner size="large" />
        <Box variant="p" color="text-body-secondary">
          Verifying authentication...
        </Box>
      </Box>
    );
  }
  
  // Redirect to login if not authenticated
  if (!user) {
    // Save the current location to redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  // Check for admin access if required
  if (requireAdmin && !user.is_admin) {
    return <Navigate to="/unauthorized" replace />;
  }
  
  // Render children if authenticated and authorized
  return <>{children}</>;
};

export default ProtectedRoute;