import React, { useState } from 'react';
import { 
  Container, 
  Header, 
  SpaceBetween, 
  Button, 
  Box,
  Grid,
  Form,
  FormField,
  Input,
  Tabs,
  Alert,
  Spinner
} from '@cloudscape-design/components';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const { login, loading, error } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();
  const [activeTabId, setActiveTabId] = useState('federated');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Handle form submission (for future direct login implementation)
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // This is a placeholder for future direct login implementation
    setTimeout(() => {
      setIsSubmitting(false);
      addNotification({
        type: 'error',
        content: 'Direct login is not implemented yet. Please use federated authentication.',
        dismissible: true,
        onDismiss: () => {}
      });
    }, 1000);
  };
  
  // Handle federated login
  const handleFederatedLogin = (provider: string) => {
    try {
      login(provider);
    } catch (err) {
      addNotification({
        type: 'error',
        content: 'Failed to initiate login. Please try again.',
        dismissible: true,
        onDismiss: () => {}
      });
    }
  };
  
  return (
    <div className="login-container">
      <Grid
        gridDefinition={[{ colspan: { default: 12, xs: 10, s: 8, m: 6, l: 4 } }]}
      >
        <Container
          header={
            <Header
              variant="h1"
              description="Connect with colleagues through virtual coffee meetings"
            >
              Virtual Coffee Platform
            </Header>
          }
        >
          <SpaceBetween size="l">
            {error && (
              <Alert
                type="error"
                header="Authentication error"
              >
                {error}
              </Alert>
            )}
            
            <Tabs
              activeTabId={activeTabId}
              onChange={({ detail }) => setActiveTabId(detail.activeTabId)}
              tabs={[
                {
                  id: 'federated',
                  label: 'Sign in with SSO',
                  content: (
                    <SpaceBetween size="l">
                      <Box variant="p">
                        Sign in with your corporate account to get started.
                      </Box>
                      
                      <SpaceBetween size="m">
                        <Button
                          variant="primary"
                          iconName="external"
                          onClick={() => handleFederatedLogin('aws-sso')}
                          fullWidth
                          disabled={loading}
                        >
                          {loading ? <Spinner /> : 'Sign in with AWS SSO'}
                        </Button>
                        
                        <Button
                          variant="normal"
                          iconName="external"
                          onClick={() => handleFederatedLogin('google')}
                          fullWidth
                          disabled={loading}
                        >
                          {loading ? <Spinner /> : 'Sign in with Google'}
                        </Button>
                      </SpaceBetween>
                    </SpaceBetween>
                  )
                },
                {
                  id: 'direct',
                  label: 'Sign in with email',
                  content: (
                    <Form
                      actions={
                        <SpaceBetween direction="horizontal" size="xs">
                          <Button 
                            variant="link" 
                            onClick={() => setActiveTabId('federated')}
                          >
                            Cancel
                          </Button>
                          <Button 
                            variant="primary" 
                            onClick={handleSubmit}
                            disabled={isSubmitting || !email || !password}
                          >
                            {isSubmitting ? <Spinner /> : 'Sign in'}
                          </Button>
                        </SpaceBetween>
                      }
                    >
                      <SpaceBetween size="l">
                        <Alert
                          type="info"
                          header="Development only"
                        >
                          Direct login is for development purposes only. In production, please use federated authentication.
                        </Alert>
                        
                        <FormField
                          label="Email"
                          description="Enter your corporate email address"
                        >
                          <Input
                            type="email"
                            value={email}
                            onChange={({ detail }) => setEmail(detail.value)}
                          />
                        </FormField>
                        
                        <FormField
                          label="Password"
                          description="Enter your password"
                        >
                          <Input
                            type="password"
                            value={password}
                            onChange={({ detail }) => setPassword(detail.value)}
                          />
                        </FormField>
                      </SpaceBetween>
                    </Form>
                  )
                }
              ]}
            />
          </SpaceBetween>
        </Container>
      </Grid>
    </div>
  );
};

export default Login;