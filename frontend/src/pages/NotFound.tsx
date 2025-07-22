import React from 'react';
import { 
  Container, 
  Header, 
  SpaceBetween, 
  Button,
  Box
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
          <Box variant="p">
            The page you are looking for does not exist or has been moved.
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