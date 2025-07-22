import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Profile from '../Profile';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import axios from 'axios';

// Mock the hooks and axios
jest.mock('../../contexts/AuthContext');
jest.mock('../../contexts/NotificationContext');
jest.mock('axios');

describe('Profile Page', () => {
  const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
  const mockUseNotifications = useNotifications as jest.MockedFunction<typeof useNotifications>;
  const mockRefreshUser = jest.fn();
  const mockAddNotification = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        is_paused: false
      },
      loading: false,
      error: null,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      refreshUser: mockRefreshUser,
      clearError: jest.fn()
    });
    
    mockUseNotifications.mockReturnValue({
      addNotification: mockAddNotification,
      removeNotification: jest.fn(),
      clearNotifications: jest.fn()
    });
  });
  
  test('renders profile information in view mode', () => {
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );
    
    expect(screen.getByText('My Profile')).toBeInTheDocument();
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Edit')).toBeInTheDocument();
  });
  
  test('switches to edit mode when Edit button is clicked', () => {
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );
    
    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);
    
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Participation status')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
    expect(screen.getByText('Save changes')).toBeInTheDocument();
  });
  
  test('updates profile information when form is submitted', async () => {
    (axios.put as jest.Mock).mockResolvedValueOnce({});
    
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );
    
    // Switch to edit mode
    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);
    
    // Update name
    const nameInput = screen.getByLabelText('Name');
    fireEvent.change(nameInput, { target: { value: 'Updated Name' } });
    
    // Submit form
    const saveButton = screen.getByText('Save changes');
    fireEvent.click(saveButton);
    
    // Check if API was called with correct data
    await waitFor(() => {
      expect(axios.put).toHaveBeenCalledWith(
        expect.stringContaining('/users/profile'),
        { name: 'Updated Name', is_paused: false },
        { withCredentials: true }
      );
    });
    
    // Check if user data was refreshed
    expect(mockRefreshUser).toHaveBeenCalled();
    
    // Check if success notification was shown
    expect(mockAddNotification).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'success',
        content: 'Profile updated successfully'
      })
    );
  });
  
  test('toggles participation status', async () => {
    (axios.put as jest.Mock).mockResolvedValueOnce({});
    
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );
    
    // Find and click the toggle
    const toggle = screen.getByText('Active');
    fireEvent.click(toggle);
    
    // Check if API was called with correct data
    await waitFor(() => {
      expect(axios.put).toHaveBeenCalledWith(
        expect.stringContaining('/users/participation'),
        { is_paused: true },
        { withCredentials: true }
      );
    });
    
    // Check if user data was refreshed
    expect(mockRefreshUser).toHaveBeenCalled();
    
    // Check if success notification was shown
    expect(mockAddNotification).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'success',
        content: 'Participation paused'
      })
    );
  });
  
  test('shows error notification when API call fails', async () => {
    (axios.put as jest.Mock).mockRejectedValueOnce(new Error('API Error'));
    
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );
    
    // Switch to edit mode
    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);
    
    // Submit form without changes
    const saveButton = screen.getByText('Save changes');
    fireEvent.click(saveButton);
    
    // Check if error notification was shown
    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'error',
          content: 'Failed to update profile'
        })
      );
    });
  });
  
  test('cancels edit mode without saving changes', () => {
    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );
    
    // Switch to edit mode
    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);
    
    // Update name
    const nameInput = screen.getByLabelText('Name');
    fireEvent.change(nameInput, { target: { value: 'Updated Name' } });
    
    // Cancel edit
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    // Check if we're back in view mode with original data
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.queryByLabelText('Name')).not.toBeInTheDocument();
    expect(axios.put).not.toHaveBeenCalled();
  });
});