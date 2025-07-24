import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppLayout as CloudscapeAppLayout,
  AppLayoutProps,
  SideNavigation,
  SideNavigationProps,
  TopNavigation,
  BreadcrumbGroup,
  BreadcrumbGroupProps,
  Flashbar,
  FlashbarProps
} from '@cloudscape-design/components';

interface AppLayoutProps {
  children: React.ReactNode;
  activeHref?: string;
  breadcrumbs?: BreadcrumbGroupProps.Item[];
  notifications?: FlashbarProps.MessageDefinition[];
  title?: string;
}

const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  activeHref,
  breadcrumbs = [],
  notifications = [],
  title = 'Virtual Coffee Platform'
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [navigationOpen, setNavigationOpen] = useState(true);

  // Define navigation items
  const navItems: SideNavigationProps.Item[] = [
    {
      type: 'section',
      text: 'Home',
      items: [
        { type: 'link', text: 'Dashboard', href: '/' }
      ]
    },
    {
      type: 'section',
      text: 'Matches',
      items: [
        { type: 'link', text: 'Current Match', href: '/matches/current' },
        { type: 'link', text: 'Match History', href: '/matches/history' }
      ]
    },
    {
      type: 'section',
      text: 'Profile',
      items: [
        { type: 'link', text: 'My Profile', href: '/profile' },
        { type: 'link', text: 'Preferences', href: '/preferences' }
      ]
    }
  ];

  // Handle navigation
  const handleNavigate: SideNavigationProps['onFollow'] = (event) => {
    event.preventDefault();
    if (event.detail.href) {
      navigate(event.detail.href);
    }
  };

  // Handle breadcrumb navigation
  const handleBreadcrumbClick: BreadcrumbGroupProps['onClick'] = (event) => {
    event.preventDefault();
    if (event.detail.href) {
      navigate(event.detail.href);
    }
  };

  return (
    <CloudscapeAppLayout
      contentType="default"
      navigation={
        <SideNavigation
          activeHref={activeHref || location.pathname}
          header={{ text: 'Virtual Coffee', href: '/' }}
          items={navItems}
          onFollow={handleNavigate}
        />
      }
      notifications={<Flashbar items={notifications} />}
      breadcrumbs={
        <BreadcrumbGroup
          items={[
            { text: 'Virtual Coffee', href: '/' },
            ...breadcrumbs
          ]}
          onClick={handleBreadcrumbClick}
        />
      }
      content={children}
      toolsHide={true}
      navigationOpen={navigationOpen}
      onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
      headerSelector="#header"
    />
  );
};

export default AppLayout;
