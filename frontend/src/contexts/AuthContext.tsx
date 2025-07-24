import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import axios from 'axios';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// User interface
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
    slack_webhook?: string;
    telegram: boolean;
    telegram_chat_id?: string;
    signal: boolean;
    signal_number?: string;
    primary_channel: string;
  };
}

// Auth context interface
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

// Provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/auth/me`, {
          withCredentials: true
        });

        if (response.data) {
          setUser(response.data);
        } else {
          setUser(null);
        }
      } catch (err) {
        console.error('Auth check error:', err);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Login function
  const login = (provider: string) => {
    setLoading(true);
    setError(null);

    // Store current path for redirect after login
    localStorage.setItem('auth_redirect', window.location.pathname);

    // Redirect to auth endpoint
    window.location.href = `${API_URL}/auth/${provider}/login`;
  };

  // Logout function
  const logout = async () => {
    try {
      setLoading(true);
      await axios.post(`${API_URL}/auth/logout`, {}, {
        withCredentials: true
      });
      setUser(null);
    } catch (err) {
      console.error('Logout error:', err);
      setError('Failed to logout');
    } finally {
      setLoading(false);
    }
  };

  // Refresh user data
  const refreshUser = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/auth/me`, {
        withCredentials: true
      });

      if (response.data) {
        setUser(response.data);
      }
    } catch (err) {
      console.error('User refresh error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Clear error
  const clearError = () => {
    setError(null);
  };

  // For development/demo purposes, always simulate a logged-in user
  useEffect(() => {
    // Using a demo user for development
    const demoUser: User = {
      id: 'demo-user-1',
      name: 'Demo User',
      email: 'demo@example.com',
      is_paused: false,
      preferences: {
        topics: ['work', 'tech', 'career'],
        availability: ['mon-am', 'wed-pm', 'fri-am'],
        meeting_length: 30
      },
      notification_prefs: {
        email: true,
        slack: false,
        telegram: false,
        signal: false,
        primary_channel: 'email'
      }
    };

    setUser(demoUser);
    setLoading(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser,
        clearError
      }}
    >
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
