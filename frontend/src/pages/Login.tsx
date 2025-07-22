import React, { useState } from 'react';
import { 
  Container, 
  Header, 
  SpaceBetween, 
  Button,
  Box,
  Alert,
  Tabs,
  Form,
  FormField,
  Input,
  Grid
} from '@cloudscape-design/components';
import { useAuth } from '../contexts/AuthContext.js';

const Login: React.FC = () => {
  const { login, loading, error, clearError } = useAuth();
  const [activeTabId, setActiveTabId] = useState('federated');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // Handle AWS SSO login
  const handleAwsSsoLogin = () => {
    login('aws-sso');
  };
  
  // Handle Google login
  const handleGoogleLogin = () => {
    login('google');
  };
  
  // Handle direct login (for development only)
  const handleDirectLogin = () => {
    // This would typically call a login API endpoint
    console.log('Direct login with:', email, password);
  };
  
  return (
    <div className="login-container">
      <Container
        header={
          <Header
            variant="h1"
            description="Connect with colleagues through automated coffee meetings"
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
              dismissible
              onDismiss={clearError}
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
                      Sign in using your corporate or Google account.
                    </Box>
                    
                    <Grid
                      gridDefinition={[
                        { colspan: { default: 12, xxs: 12, xs: 6 } },
                        { colspan: { default: 12, xxs: 12, xs: 6 } }
                      ]}
                    >
                      <Button
                        variant="primary"
                        iconName="external"
                        fullWidth
                        onClick={handleAwsSsoLogin}
                        loading={loading}
                        disabled={loading}
                      >
                        Sign in with AWS SSO
                      </Button>
                      
                      <Button
                        variant="normal"
                        iconName="external"
                        fullWidth
                        onClick={handleGoogleLogin}
                        loading={loading}
                        disabled={loading}
                      >
                        Sign in with Google
                      </Button>
                    </Grid>
                  </SpaceBetween>
                )
              },
              {
                id: 'direct',
                label: 'Sign in with email',
                content: (
                  <Form
                    actions={
                      <Button
                        variant="primary"
                        onClick={handleDirectLogin}
                        loading={loading}
                        disabled={loading}
                      >
                        Sign in
                      </Button>
                    }
                  >
                    <SpaceBetween size="l">
                      <Alert
                        type="info"
                        header="Development only"
                      >
                        Direct login is only available in development mode.
                      </Alert>
                      
                      <FormField
                        label="Email"
                        description="Enter your email address"
                      >
                        <Input
                          value={email}
                          onChange={({ detail }) => setEmail(detail.value)}
                          type="email"
                        />
                      </FormField>
                      
                      <FormField
                        label="Password"
                        description="Enter your password"
                      >
                        <Input
                          value={password}
                          onChange={({ detail }) => setPassword(detail.value)}
                          type="password"
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
    </div>
  );
};

export default Login;