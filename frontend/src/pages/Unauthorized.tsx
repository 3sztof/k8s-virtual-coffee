import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Button,
  Box,
  Alert
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';

const Unauthorized: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="not-found-container">
      <Container
        header={
          <Header
            variant="h1"
          >
            Access denied
          </Header>
        }
      >
        <SpaceBetween size="l">
          <Alert
            type="error"
            header="Insufficient permissions"
          >
            You do not have the required permissions to access this page.
          </Alert>

          <Box variant="p">
            Please contact your administrator if you believe this is an error.
          </Box>

          <Button
            onClick={() => navigate('/')}
          >
            Go to Dashboard
          </Button>
        </SpaceBetween>
      </Container>
    </div>
  );
};

export default Unauthorized;
