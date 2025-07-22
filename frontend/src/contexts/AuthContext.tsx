import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

// Define types
interface User {
  id: string;
  name: string;
  email: string;
  is_paused: boolean;
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

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (provider: string) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/auth/me`, {
          withCredentials: true
        });
        setUser(response.data);
        setError(null);
      } catch (err) {
        setUser(null);
        // Don't set error on initial load if not authenticated
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // Login function
  const login = (provider: string) => {
    // Get deployment ID from URL or use default
    const urlParams = new URLSearchParams(window.location.search);
    const deploymentId = urlParams.get('deployment') || 'default';
    
    // Redirect to OAuth provider
    window.location.href = `${API_URL}/auth/${provider}?deployment_id=${deploymentId}`;
  };

  // Logout function
  const logout = async () => {
    try {
      await axios.post(`${API_URL}/auth/logout`, {}, {
        withCredentials: true
      });
      setUser(null);
    } catch (err) {
      setError('Failed to logout');
      console.error('Logout error:', err);
    }
  };

  // Refresh user data
  const refreshUser = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/auth/me`, {
        withCredentials: true
      });
      setUser(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to refresh user data');
      console.error('Refresh user error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout, refreshUser }}>
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