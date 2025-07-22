import React from 'react';
import { TopNavigation } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  username?: string;
  onSignOut?: () => void;
}

const Header: React.FC<HeaderProps> = ({ username, onSignOut }) => {
  const navigate = useNavigate();

  const handleSignOut = () => {
    if (onSignOut) {
      onSignOut();
    }
  };

  return (
    <div id="header">
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
            text: username || 'Account',
            description: username || 'User',
            iconName: 'user-profile',
            items: [
              { id: 'profile', text: 'My profile', href: '/profile' },
              { id: 'preferences', text: 'Preferences', href: '/preferences' },
              { id: 'signout', text: 'Sign out', onClick: handleSignOut }
            ]
          }
        ]}
        i18nStrings={{
          searchIconAriaLabel: 'Search',
          searchDismissIconAriaLabel: 'Close search',
          overflowMenuTriggerText: 'More',
          overflowMenuTitleText: 'All',
          overflowMenuBackIconAriaLabel: 'Back',
          overflowMenuDismissIconAriaLabel: 'Close menu'
        }}
      />
    </div>
  );
};

export default Header;