import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../Dashboard';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import axios from 'axios';

// Mock the hooks and axios
jest.mock('../../contexts/AuthContext');
jest.mock('../../contexts/NotificationContext');
jest.mock('axios');

describe('Dashboard Page', () => {
  const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
  const mockUseNotifications = useNotifications as jest.MockedFunction<typeof useNotifications>;
  const mockAddNotification = jest.fn();
  
  // Mock data
  const mockUser = {
    id: 'user-1',
    name: 'Test User',
    email: 'test@example.com',
    is_paused: false
  };
  
  const mockCurrentMatch = {
    id: 'match-1',
    participants: [
      { id: 'user-1', name: 'Test User', email: 'test@example.com' },
      { id: 'user-2', name: 'Coffee Partner', email: 'partner@example.com' }
    ],
    scheduled_date: '2025-07-25T10:00:00Z',
    status: 'scheduled',
    created_at: '2025-07-22T08:00:00Z'
  };
  
  const mockMatchHistory = {
    matches: [
      {
        id: 'match-2',
        participants: [
          { id: 'user-1', name: 'Test User', email: 'test@example.com' },
          { id: 'user-3', name: 'Past Partner', email: 'past@example.com' }
        ],
        scheduled_date: '2025-07-15T10:00:00Z',
        status: 'completed',
        created_at: '2025-07-12T08:00:00Z',
        feedback: {
          rating: 5,
          comments: 'Great conversation!'
        }
      }
    ],
    total_pages: 1
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock auth context
    mockUseAuth.mockReturnValue({
      user: mockUser,
      loading: false,
      error: null,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
      clearError: jest.fn()
    });
    
    // Mock notifications context
    mockUseNotifications.mockReturnValue({
      addNotification: mockAddNotification,
      removeNotification: jest.fn(),
      clearNotifications: jest.fn()
    });
    
    // Mock axios responses
    (axios.get as jest.Mock).mockImplementation((url) => {
      if (url.includes('/matches/current')) {
        return Promise.resolve({ data: mockCurrentMatch });
      } else if (url.includes('/matches/history')) {
        return Promise.resolve({ data: mockMatchHistory });
      }
      return Promise.reject(new Error('Not found'));
    });
  });
  
  test('renders dashboard with user information', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Check user greeting
    expect(screen.getByText(/Hello, Test User!/i)).toBeInTheDocument();
    
    // Check status
    expect(screen.getByText('Active')).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/matches/current'),
        expect.anything()
      );
    });
  });
  
  test('displays current match when available', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Wait for current match to load
    await waitFor(() => {
      expect(screen.getByText(/Coffee Partner/i)).toBeInTheDocument();
    });
    
    // Check match details
    expect(screen.getByText(/partner@example.com/i)).toBeInTheDocument();
    expect(screen.getByText('Scheduled')).toBeInTheDocument();
  });
  
  test('displays match history', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Wait for match history to load
    await waitFor(() => {
      expect(screen.getByText('Match History')).toBeInTheDocument();
    });
    
    // Check history table
    expect(screen.getByText(/Past Partner/i)).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('5/5')).toBeInTheDocument();
  });
  
  test('opens feedback modal when Add feedback button is clicked', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Wait for current match to load
    await waitFor(() => {
      expect(screen.getByText(/Coffee Partner/i)).toBeInTheDocument();
    });
    
    // Find and click Add feedback button
    const addFeedbackButton = screen.getAllByText('Add feedback')[0];
    fireEvent.click(addFeedbackButton);
    
    // Check if modal is open
    expect(screen.getByText('Match Feedback')).toBeInTheDocument();
    expect(screen.getByText(/How would you rate this coffee meeting?/i)).toBeInTheDocument();
  });
  
  test('opens status update modal when Update status button is clicked', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Wait for current match to load
    await waitFor(() => {
      expect(screen.getByText(/Coffee Partner/i)).toBeInTheDocument();
    });
    
    // Find and click Update status button
    const updateStatusButton = screen.getAllByText('Update status')[0];
    fireEvent.click(updateStatusButton);
    
    // Check if modal is open
    expect(screen.getByText('Update Match Status')).toBeInTheDocument();
    expect(screen.getByText(/Select the current status of this coffee meeting/i)).toBeInTheDocument();
  });
  
  test('submits feedback successfully', async () => {
    // Mock successful feedback submission
    (axios.post as jest.Mock).mockResolvedValueOnce({});
    
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Wait for current match to load
    await waitFor(() => {
      expect(screen.getByText(/Coffee Partner/i)).toBeInTheDocument();
    });
    
    // Find and click Add feedback button
    const addFeedbackButton = screen.getAllByText('Add feedback')[0];
    fireEvent.click(addFeedbackButton);
    
    // Select rating
    const ratingSelect = screen.getByPlaceholderText('Select a rating');
    fireEvent.click(ratingSelect);
    
    // Wait for dropdown to appear and select an option
    await waitFor(() => {
      const option = screen.getByText('5 - Excellent');
      fireEvent.click(option);
    });
    
    // Add comments
    const commentsTextarea = screen.getByPlaceholderText('Optional comments');
    fireEvent.change(commentsTextarea, { target: { value: 'Great meeting!' } });
    
    // Submit feedback
    const submitButton = screen.getByText('Submit feedback');
    fireEvent.click(submitButton);
    
    // Check if API was called with correct data
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/matches/feedback'),
        {
          match_id: 'match-1',
          rating: 5,
          comments: 'Great meeting!'
        },
        { withCredentials: true }
      );
    });
    
    // Check if success notification was shown
    expect(mockAddNotification).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'success',
        content: 'Feedback submitted successfully'
      })
    );
  });
  
  test('updates match status successfully', async () => {
    // Mock successful status update
    (axios.put as jest.Mock).mockResolvedValueOnce({});
    
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Wait for current match to load
    await waitFor(() => {
      expect(screen.getByText(/Coffee Partner/i)).toBeInTheDocument();
    });
    
    // Find and click Update status button
    const updateStatusButton = screen.getAllByText('Update status')[0];
    fireEvent.click(updateStatusButton);
    
    // Select status
    const statusSelect = screen.getByPlaceholderText('Select a status');
    fireEvent.click(statusSelect);
    
    // Wait for dropdown to appear and select an option
    await waitFor(() => {
      const option = screen.getByText('Completed');
      fireEvent.click(option);
    });
    
    // Submit status update
    const updateButton = screen.getByText('Update status', { selector: 'button[variant="primary"]' });
    fireEvent.click(updateButton);
    
    // Check if API was called with correct data
    await waitFor(() => {
      expect(axios.put).toHaveBeenCalledWith(
        expect.stringContaining('/matches/match-1/status'),
        { status: 'completed' },
        { withCredentials: true }
      );
    });
    
    // Check if success notification was shown
    expect(mockAddNotification).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'success',
        content: 'Match status updated successfully'
      })
    );
  });
  
  test('shows empty state when no current match is available', async () => {
    // Override the mock to return no current match
    (axios.get as jest.Mock).mockImplementation((url) => {
      if (url.includes('/matches/current')) {
        return Promise.resolve({ data: null });
      } else if (url.includes('/matches/history')) {
        return Promise.resolve({ data: mockMatchHistory });
      }
      return Promise.reject(new Error('Not found'));
    });
    
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('No current match')).toBeInTheDocument();
    });
    
    expect(screen.getByText("You don't have any active coffee matches at the moment.")).toBeInTheDocument();
  });
  
  test('shows paused message when user is paused', async () => {
    // Override the mock to return paused user
    mockUseAuth.mockReturnValue({
      user: { ...mockUser, is_paused: true },
      loading: false,
      error: null,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
      clearError: jest.fn()
    });
    
    // Override the mock to return no current match
    (axios.get as jest.Mock).mockImplementation((url) => {
      if (url.includes('/matches/current')) {
        return Promise.resolve({ data: null });
      } else if (url.includes('/matches/history')) {
        return Promise.resolve({ data: mockMatchHistory });
      }
      return Promise.reject(new Error('Not found'));
    });
    
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Paused')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Participation paused')).toBeInTheDocument();
  });
});