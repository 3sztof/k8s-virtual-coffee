import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';

// Define types
interface User {
  id: string;
  name: string;
  email: string;
  is_paused: boolean;
  is_admin?: boolean;
  preferences?: {
    topics: string[];
    availability: string[];
    meeting_length: number;
  };
  notification_prefs?: {
    email: boolean;
    slack: boolean;
    telegram: boolean;
    signal: boolean;
    primary_channel: string;
  };
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (provider: string) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Setup axios interceptor for authentication
const setupAxiosInterceptors = (logout: () => void) => {
  axios.interceptors.response.use(
    response => response,
    error => {
      if (error.response && error.response.status === 401) {
        // Auto logout if 401 response returned from API
        logout();
      }
      return Promise.reject(error);
    }
  );
};

// Provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    token: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Logout function
  const logout = useCallback(async () => {
    try {
      await axios.post(`${API_URL}/auth/logout`, {}, {
        withCredentials: true
      });
      
      // Clear auth state
      setAuthState({
        isAuthenticated: false,
        user: null,
        token: null
      });
      
      // Clear any stored tokens
      localStorage.removeItem('auth_token');
      
      // Redirect to login
      navigate('/login');
    } catch (err) {
      setError('Failed to logout');
      console.error('Logout error:', err);
    }
  }, [navigate]);

  // Setup axios interceptors
  useEffect(() => {
    setupAxiosInterceptors(logout);
  }, [logout]);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      try {
        setLoading(true);
        
        // Check for token in URL (OAuth callback)
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        
        if (token) {
          // Store token and remove from URL
          localStorage.setItem('auth_token', token);
          navigate(location.pathname, { replace: true });
        }
        
        // Try to get user data
        const storedToken = localStorage.getItem('auth_token');
        
        if (storedToken) {
          // Set auth header
          axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          
          // Get user data
          const response = await axios.get(`${API_URL}/auth/me`, {
            withCredentials: true
          });
          
          setAuthState({
            isAuthenticated: true,
            user: response.data,
            token: storedToken
          });
          
          setError(null);
        } else {
          // No token found
          setAuthState({
            isAuthenticated: false,
            user: null,
            token: null
          });
        }
      } catch (err) {
        // Clear invalid auth state
        setAuthState({
          isAuthenticated: false,
          user: null,
          token: null
        });
        
        localStorage.removeItem('auth_token');
        
        // Don't set error on initial load if not authenticated
        if (localStorage.getItem('auth_token')) {
          setError('Authentication session expired');
        }
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, [location.pathname, navigate]);

  // Login function
  const login = (provider: string) => {
    // Get deployment ID from URL or use default
    const urlParams = new URLSearchParams(window.location.search);
    const deploymentId = urlParams.get('deployment') || 'default';
    
    // Store current location for redirect after login
    const returnTo = location.pathname !== '/login' ? location.pathname : '/';
    localStorage.setItem('auth_redirect', returnTo);
    
    // Redirect to OAuth provider
    window.location.href = `${API_URL}/auth/${provider}?deployment_id=${deploymentId}&redirect_uri=${window.location.origin}/login`;
  };

  // Refresh user data
  const refreshUser = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/auth/me`, {
        withCredentials: true
      });
      
      setAuthState(prev => ({
        ...prev,
        user: response.data
      }));
      
      setError(null);
    } catch (err) {
      setError('Failed to refresh user data');
      console.error('Refresh user error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Clear error
  const clearError = () => {
    setError(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user: authState.user, 
      loading, 
      error, 
      isAuthenticated: authState.isAuthenticated,
      login, 
      logout, 
      refreshUser,
      clearError
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};