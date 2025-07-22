import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  AppLayout, 
  SideNavigation, 
  Container, 
  ContentLayout,
  SpaceBetween,
  BreadcrumbGroup
} from '@cloudscape-design/components';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeHref, setActiveHref] = useState(window.location.pathname);
  
  // Handle navigation
  const handleNavigate = (href: string) => {
    setActiveHref(href);
    navigate(href);
  };
  
  // Handle sign out
  const handleSignOut = () => {
    logout();
    navigate('/login');
  };
  
  // Get current page title
  const getPageTitle = () => {
    switch (activeHref) {
      case '/':
        return 'Dashboard';
      case '/profile':
        return 'My Profile';
      case '/preferences':
        return 'Preferences';
      default:
        return 'Virtual Coffee Platform';
    }
  };
  
  // Breadcrumb items
  const breadcrumbItems = [
    { text: 'Home', href: '/' },
    { text: getPageTitle(), href: activeHref }
  ];
  
  return (
    <div>
      <Header 
        username={user?.name} 
        onSignOut={handleSignOut} 
      />
      <AppLayout
        content={
          <ContentLayout
            header={
              <SpaceBetween size="m">
                <BreadcrumbGroup items={breadcrumbItems} />
                <h1>{getPageTitle()}</h1>
              </SpaceBetween>
            }
          >
            <Container>
              {children}
            </Container>
          </ContentLayout>
        }
        navigation={
          <SideNavigation
            activeHref={activeHref}
            header={{ text: 'Navigation', href: '/' }}
            items={[
              { type: 'link', text: 'Dashboard', href: '/', onClick: () => handleNavigate('/') },
              { type: 'link', text: 'My Profile', href: '/profile', onClick: () => handleNavigate('/profile') },
              { type: 'link', text: 'Preferences', href: '/preferences', onClick: () => handleNavigate('/preferences') },
            ]}
          />
        }
        toolsHide={true}
        navigationWidth={300}
        contentType="default"
      />
    </div>
  );
};

export default MainLayout;