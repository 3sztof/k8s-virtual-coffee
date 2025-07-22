import React, { useState } from 'react';
import { 
  Container, 
  Header, 
  SpaceBetween, 
  Box, 
  ColumnLayout,
  Form,
  FormField,
  Input,
  Button,
  Toggle,
  Alert,
  Spinner
} from '@cloudscape-design/components';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import axios from 'axios';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Profile: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const { addNotification } = useNotifications();
  
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(user?.name || '');
  const [isPaused, setIsPaused] = useState(user?.is_paused || false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Handle form submission
  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      
      // Update user profile
      await axios.put(`${API_URL}/users/profile`, {
        name,
        is_paused: isPaused
      }, {
        withCredentials: true
      });
      
      // Refresh user data
      await refreshUser();
      
      // Show success notification
      addNotification({
        type: 'success',
        content: 'Profile updated successfully',
        dismissible: true,
        onDismiss: () => {}
      });
      
      // Exit edit mode
      setIsEditing(false);
    } catch (err) {
      // Show error notification
      addNotification({
        type: 'error',
        content: 'Failed to update profile',
        dismissible: true,
        onDismiss: () => {}
      });
      console.error('Profile update error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle cancel
  const handleCancel = () => {
    // Reset form values
    setName(user?.name || '');
    setIsPaused(user?.is_paused || false);
    setIsEditing(false);
  };
  
  // Handle participation toggle
  const handlePauseToggle = async (checked: boolean) => {
    setIsPaused(checked);
    
    if (!isEditing) {
      try {
        setIsSubmitting(true);
        
        // Update participation status
        await axios.put(`${API_URL}/users/participation`, {
          is_paused: checked
        }, {
          withCredentials: true
        });
        
        // Refresh user data
        await refreshUser();
        
        // Show success notification
        addNotification({
          type: 'success',
          content: checked ? 'Participation paused' : 'Participation resumed',
          dismissible: true,
          onDismiss: () => {}
        });
      } catch (err) {
        // Show error notification
        addNotification({
          type: 'error',
          content: 'Failed to update participation status',
          dismissible: true,
          onDismiss: () => {}
        });
        console.error('Participation update error:', err);
        
        // Reset toggle
        setIsPaused(!checked);
      } finally {
        setIsSubmitting(false);
      }
    }
  };
  
  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header
            variant="h2"
            description="Manage your profile information"
            actions={
              isEditing ? (
                <SpaceBetween direction="horizontal" size="xs">
                  <Button onClick={handleCancel}>Cancel</Button>
                  <Button 
                    variant="primary" 
                    onClick={handleSubmit}
                    loading={isSubmitting}
                  >
                    Save changes
                  </Button>
                </SpaceBetween>
              ) : (
                <Button onClick={() => setIsEditing(true)}>Edit</Button>
              )
            }
          >
            My Profile
          </Header>
        }
      >
        {isEditing ? (
          <Form>
            <SpaceBetween size="l">
              <FormField
                label="Name"
                description="Your display name"
              >
                <Input
                  value={name}
                  onChange={({ detail }) => setName(detail.value)}
                />
              </FormField>
              
              <FormField
                label="Email"
                description="Your email address (cannot be changed)"
              >
                <Input
                  value={user?.email || ''}
                  disabled
                />
              </FormField>
              
              <FormField
                label="Participation status"
                description="Toggle to pause or resume your participation in coffee meetings"
              >
                <Toggle
                  checked={!isPaused}
                  onChange={({ detail }) => handlePauseToggle(!detail.checked)}
                >
                  {isPaused ? 'Paused' : 'Active'}
                </Toggle>
              </FormField>
            </SpaceBetween>
          </Form>
        ) : (
          <SpaceBetween size="l">
            <ColumnLayout columns={2} variant="text-grid">
              <div>
                <Box variant="awsui-key-label">Name</Box>
                <div>{user?.name}</div>
              </div>
              <div>
                <Box variant="awsui-key-label">Email</Box>
                <div>{user?.email}</div>
              </div>
              <div>
                <Box variant="awsui-key-label">Status</Box>
                <div>
                  <Toggle
                    checked={!user?.is_paused}
                    onChange={({ detail }) => handlePauseToggle(!detail.checked)}
                    disabled={isSubmitting}
                  >
                    {user?.is_paused ? 'Paused' : 'Active'}
                  </Toggle>
                </div>
              </div>
            </ColumnLayout>
            
            {user?.is_paused && (
              <Alert
                type="info"
                header="Participation paused"
              >
                You are currently not participating in coffee meetings. Toggle the status above to resume participation.
              </Alert>
            )}
          </SpaceBetween>
        )}
      </Container>
    </SpaceBetween>
  );
};

export default Profile;