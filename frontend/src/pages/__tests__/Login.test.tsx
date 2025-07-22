import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../Login';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';

// Mock the hooks
jest.mock('../../contexts/AuthContext');
jest.mock('../../contexts/NotificationContext');

describe('Login Page', () => {
  const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
  const mockUseNotifications = useNotifications as jest.MockedFunction<typeof useNotifications>;
  const mockLogin = jest.fn();
  const mockAddNotification = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      error: null,
      isAuthenticated: false,
      login: mockLogin,
      logout: jest.fn(),
      refreshUser: jest.fn(),
      clearError: jest.fn()
    });
    
    mockUseNotifications.mockReturnValue({
      addNotification: mockAddNotification,
      removeNotification: jest.fn(),
      clearNotifications: jest.fn()
    });
  });
  
  test('renders login page with SSO options', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    expect(screen.getByText('Virtual Coffee Platform')).toBeInTheDocument();
    expect(screen.getByText('Sign in with AWS SSO')).toBeInTheDocument();
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument();
  });
  
  test('calls login function when AWS SSO button is clicked', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    const awsSsoButton = screen.getByText('Sign in with AWS SSO');
    fireEvent.click(awsSsoButton);
    
    expect(mockLogin).toHaveBeenCalledWith('aws-sso');
  });
  
  test('calls login function when Google button is clicked', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    const googleButton = screen.getByText('Sign in with Google');
    fireEvent.click(googleButton);
    
    expect(mockLogin).toHaveBeenCalledWith('google');
  });
  
  test('displays error alert when authentication error occurs', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      error: 'Authentication failed',
      isAuthenticated: false,
      login: mockLogin,
      logout: jest.fn(),
      refreshUser: jest.fn(),
      clearError: jest.fn()
    });
    
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    expect(screen.getByText('Authentication error')).toBeInTheDocument();
    expect(screen.getByText('Authentication failed')).toBeInTheDocument();
  });
  
  test('switches between tabs when clicked', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    // Initially on federated tab
    expect(screen.getByText('Sign in with AWS SSO')).toBeInTheDocument();
    
    // Click on direct login tab
    const directLoginTab = screen.getByText('Sign in with email');
    fireEvent.click(directLoginTab);
    
    // Should show direct login form
    expect(screen.getByText('Development only')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });
  
  test('shows loading state when authentication is in progress', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: true,
      error: null,
      isAuthenticated: false,
      login: mockLogin,
      logout: jest.fn(),
      refreshUser: jest.fn(),
      clearError: jest.fn()
    });
    
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    // Buttons should be disabled during loading
    const awsSsoButton = screen.getByText('Sign in with AWS SSO').closest('button');
    expect(awsSsoButton).toBeDisabled();
    
    const googleButton = screen.getByText('Sign in with Google').closest('button');
    expect(googleButton).toBeDisabled();
  });
});