---
sidebar_position: 2
---

# User Management

As an administrator, you have access to comprehensive user management features to oversee user accounts and participation.

## Accessing User Management

To access user management features:

1. Log in to the platform with your administrator account
2. Click on "Admin" in the navigation menu
3. Select "Users" from the admin menu

## User Overview

The Users page provides a complete overview of all users in your deployment:

- Total number of users
- Active vs. paused users
- Recent registrations
- User participation statistics

## Viewing Users

The user list displays all users in your deployment with key information:

- Name and email
- Department/team
- Registration date
- Participation status (active/paused)
- Last activity date

### Filtering and Sorting

You can filter and sort the user list by:

- Status (active, paused, all)
- Department or team
- Registration date
- Participation rate
- Match history

### User Search

Use the search function to quickly find specific users:

1. Enter a name, email, or department in the search box
2. The list will filter in real-time to show matching users

## Managing Individual Users

### Viewing User Details

To view detailed information about a user:

1. Click on the user's name in the user list
2. The user profile page shows:
   - Personal information
   - Preferences and availability
   - Match history
   - Feedback provided
   - Participation statistics

### Editing User Information

To edit a user's information:

1. Navigate to the user's profile
2. Click "Edit" in the top-right corner
3. Update the necessary fields
4. Click "Save" to apply changes

You can edit:
- Name and contact information
- Department/team assignment
- Profile picture
- Notes (visible only to administrators)

### Managing User Preferences

As an administrator, you can view and modify user preferences:

1. Navigate to the user's profile
2. Click the "Preferences" tab
3. View or modify their:
   - Availability
   - Topics of interest
   - Meeting length preference
   - Notification settings
4. Click "Save" to apply changes

:::caution
Modifying user preferences should be done sparingly and ideally with the user's consent.
:::

### Toggling Participation

To enable or disable a user's participation:

1. Navigate to the user's profile
2. Use the "Participation" toggle switch
3. If disabling, you can set a reason and duration
4. Click "Save" to apply the change

This is useful for:
- Onboarding new employees
- Managing temporary leaves
- Offboarding departing employees

### Deleting Users

To delete a user:

1. Navigate to the user's profile
2. Click "Actions" in the top-right corner
3. Select "Delete User"
4. Confirm the deletion

:::danger
User deletion is permanent and cannot be undone. Consider disabling participation instead for temporary situations.
:::

## Bulk Operations

### Importing Users

To import multiple users at once:

1. Navigate to the Users page
2. Click "Import Users"
3. Download the CSV template
4. Fill in the template with user information
5. Upload the completed CSV file
6. Review the import preview
7. Click "Import" to create the accounts

The CSV format should be:
```
email,name,department
user1@example.com,John Doe,Engineering
user2@example.com,Jane Smith,Marketing
```

### Exporting Users

To export user data:

1. Navigate to the Users page
2. Apply any desired filters
3. Click "Export"
4. Choose the export format (CSV or JSON)
5. Select the data fields to include
6. Click "Download"

This is useful for:
- Reporting
- Backup
- Analysis in external tools

### Bulk Actions

You can perform actions on multiple users at once:

1. Select users by checking the boxes next to their names
2. Click "Bulk Actions"
3. Choose an action:
   - Enable participation
   - Disable participation
   - Change department
   - Send notification
   - Delete users
4. Configure the action settings
5. Click "Apply" to execute

## User Analytics

The user management section provides analytics on user engagement:

- Participation rates over time
- Match completion statistics
- Feedback ratings distribution
- Activity heatmap by day/time

These analytics help you understand how users are engaging with the platform and identify areas for improvement.
