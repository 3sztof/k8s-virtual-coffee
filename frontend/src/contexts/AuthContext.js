import React, { createContext, useState, useContext, useEffect } from 'react';

// Create context
const AuthContext = createContext();

// Provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // For development/demo purposes, always simulate a logged-in user
  useEffect(() => {
    // Using a demo user for development
    const demoUser = {
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
  
  // Login function
  const login = (provider) => {
    setLoading(true);
    setError(null);
    
    // Store current path for redirect after login
    localStorage.setItem('auth_redirect', window.location.pathname);
    
    // For demo, just set the user directly
    setTimeout(() => {
      setUser({
        id: 'demo-user-1',
        name: 'Demo User',
        email: 'demo@example.com',
        is_paused: false
      });
      setLoading(false);
    }, 1000);
  };
  
  // Logout function
  const logout = async () => {
    try {
      setLoading(true);
      // For demo, just clear the user
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
      // For demo, just set the user again
      setUser({
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
      });
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