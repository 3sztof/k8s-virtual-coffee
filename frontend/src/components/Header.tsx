import React from 'react';
import { TopNavigation } from '@cloudscape-design/components';

interface HeaderProps {
  username?: string;
  onSignOut: () => void;
}

const Header: React.FC<HeaderProps> = ({ username, onSignOut }) => {
  return (
    <TopNavigation
      identity={{
        href: '/',
        title: 'Virtual Coffee Platform',
        logo: {
          src: '/logo.png',
          alt: 'Virtual Coffee Platform'
        }
      }}
      utilities={[
        {
          type: 'menu-dropdown',
          text: username || 'User',
          description: username,
          iconName: 'user-profile',
          items: [
            { id: 'profile', text: 'My profile', href: '/profile' },
            { id: 'preferences', text: 'Preferences', href: '/preferences' },
            { id: 'signout', text: 'Sign out', href: '#', onFollow: onSignOut }
          ]
        }
      ]}
    />
  );
};

export default Header;
