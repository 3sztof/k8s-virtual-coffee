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

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <div className="not-found-container">
      <Container
        header={
          <Header
            variant="h1"
          >
            Page not found
          </Header>
        }
      >
        <SpaceBetween size="l">
          <Alert
            type="warning"
            header="404 Error"
          >
            The page you are looking for does not exist.
          </Alert>
          
          <Box variant="p">
            Please check the URL or navigate back to the dashboard.
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

export default NotFound;