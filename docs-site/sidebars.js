/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // By default, Docusaurus generates a sidebar from the docs folder structure
  userSidebar: [
    {
      type: 'category',
      label: 'User Guide',
      items: [
        'user-guide/introduction',
        'user-guide/getting-started',
        'user-guide/preferences',
        'user-guide/matches',
        'user-guide/notifications',
        'user-guide/troubleshooting',
      ],
    },
  ],
  
  adminSidebar: [
    {
      type: 'category',
      label: 'Admin Guide',
      items: [
        'admin-guide/introduction',
        'admin-guide/user-management',
        'admin-guide/match-administration',
        'admin-guide/configuration',
        'admin-guide/monitoring',
        'admin-guide/troubleshooting',
      ],
    },
  ],
  
  deploymentSidebar: [
    {
      type: 'category',
      label: 'Deployment',
      items: [
        'deployment/installation',
        'deployment/makefile-usage',
        'deployment/operations',
        'deployment/troubleshooting',
        'deployment/crossplane-resources',
        'deployment/validation',
      ],
    },
  ],
};

module.exports = sidebars;