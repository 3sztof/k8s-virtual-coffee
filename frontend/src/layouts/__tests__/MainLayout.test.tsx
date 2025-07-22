import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MainLayout from '../MainLayout';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the auth context
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { name: 'Test User', email: 'test@example.com', is_paused: false },
    logout: jest.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('MainLayout', () => {
  test('renders the layout with navigation', () => {
    render(
      <BrowserRouter>
        <MainLayout>
          <div data-testid="test-content">Test Content</div>
        </MainLayout>
      </BrowserRouter>
    );
    
    // Check if the content is rendered
    expect(screen.getByTestId('test-content')).toBeInTheDocument();
    
    // Check if navigation elements are present
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('My Profile')).toBeInTheDocument();
    expect(screen.getByText('Preferences')).toBeInTheDocument();
  });
});