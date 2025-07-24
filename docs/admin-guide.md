# Virtual Coffee Platform - Administrator Guide

This guide provides detailed instructions for administrators managing Virtual Coffee Platform deployments.

## Administrator Responsibilities

As an administrator of the Virtual Coffee Platform, you are responsible for:

1. **Deployment Management**: Setting up and maintaining platform instances
2. **Configuration**: Customizing the platform for your team or organization
3. **User Management**: Overseeing user accounts and participation
4. **Monitoring**: Ensuring the platform is running smoothly
5. **Troubleshooting**: Addressing issues that may arise

## Deployment Administration

### Accessing Admin Features

Admin features are available to users designated as administrators in the deployment configuration:

1. **Admin Dashboard**:
   - Log in to the platform
   - Click on "Admin" in the navigation menu (only visible to admins)

2. **Admin API Access**:
   - Use the admin API endpoints with appropriate authentication
   - Admin tokens have elevated privileges

### Deployment Configuration

Configure your deployment through the admin interface or by updating the configuration files:

1. **Through Admin Interface**:
   - Navigate to "Admin" > "Configuration"
   - Update settings as needed
   - Click "Save" to apply changes

2. **Through GitOps Workflow**:
   - Update configuration files in the Git repository
   - Commit and push changes
   - ArgoCD will automatically apply the changes

### Key Configuration Parameters

#### Matching Schedule

Configure when matching occurs:

```yaml
schedule:
  cron: "0 0 * * 1"  # Every Monday at midnight UTC
  timezone: "America/Los_Angeles"
```

#### Meeting Size

Configure the size of coffee meetings:

```yaml
matching:
  meetingSize: 2  # Pairs (default)
  # meetingSize: 3  # Groups of three
```

#### Email Templates

Customize email notification templates:

```yaml
emailTemplates:
  matchNotification: |
    Hello {{name}},

    You've been matched with {{match_names}} for a virtual coffee chat!

    Suggested times based on your availability:
    {{suggested_times}}

    Please coordinate directly to schedule your meeting.

    Best regards,
    The Virtual Coffee Platform
```

#### Authentication Providers

Configure authentication providers:

```yaml
auth:
  awsSso:
    enabled: true
    region: "us-west-2"
    startUrl: "https://your-org.awsapps.com/start"

  google:
    enabled: true
    clientId: "your-client-id"
    allowedDomains: ["yourcompany.com"]
```

## User Management

### Viewing Users

Access user information through the admin dashboard:

1. Navigate to "Admin" > "Users"
2. View a list of all users in your deployment
3. Filter by status, department, or other attributes
4. Export user data if needed

### Managing User Accounts

Perform user management tasks:

1. **View User Details**:
   - Click on a user's name to view their profile
   - See their preferences, match history, and participation status

2. **Edit User Information**:
   - Update user details if necessary
   - Reset preferences if requested

3. **Toggle Participation**:
   - Enable or disable a user's participation
   - Useful for onboarding/offboarding

4. **Delete User**:
   - Remove a user from the platform
   - This action cannot be undone

### Bulk Operations

Perform actions on multiple users:

1. **Import Users**:
   - Upload a CSV file with user information
   - Format: `email,name,department`
   - Users will receive invitation emails

2. **Export Users**:
   - Download user data as CSV or JSON
   - Useful for reporting or backup

3. **Bulk Enable/Disable**:
   - Select multiple users
   - Enable or disable their participation

## Matching Administration

### Manual Matching

Trigger matching manually if needed:

1. Navigate to "Admin" > "Matching"
2. Click "Run Matching Now"
3. Confirm the action

This will run the matching algorithm immediately, regardless of the scheduled time.

### Viewing Matches

Review current and past matches:

1. Navigate to "Admin" > "Matches"
2. View all matches in your deployment
3. Filter by date, status, or participants
4. Export match data if needed

### Adjusting Matches

Make changes to matches if necessary:

1. **Edit Match**:
   - Click on a match to view details
   - Click "Edit" to make changes

2. **Reassign Participants**:
   - Add or remove participants from a match
   - Useful for handling special requests

3. **Cancel Match**:
   - Mark a match as canceled
   - Optionally provide a reason

4. **Rematch Users**:
   - Select users who need to be rematched
   - Click "Create New Match" to generate a match outside the regular schedule

## Monitoring and Analytics

### Dashboard Overview

The admin dashboard provides key metrics:

1. **Participation Rate**:
   - Percentage of active users
   - Trend over time

2. **Match Completion Rate**:
   - Percentage of matches that were completed
   - Trend over time

3. **User Satisfaction**:
   - Average feedback rating
   - Trend over time

4. **System Health**:
   - API response time
   - Database status
   - Notification delivery success rate

### Detailed Analytics

Access more detailed analytics:

1. Navigate to "Admin" > "Analytics"
2. View charts and graphs for various metrics
3. Filter by date range, department, or other attributes
4. Export data for further analysis

### Logs and Audit Trail

Review system logs and user actions:

1. Navigate to "Admin" > "Logs"
2. View system logs, error messages, and user actions
3. Filter by severity, component, or date
4. Export logs for troubleshooting

## Notification Management

### Email Configuration

Configure email settings:

1. Navigate to "Admin" > "Notifications" > "Email"
2. Update SMTP settings or AWS SES configuration
3. Customize email templates
4. Test email delivery

### Additional Channels

Configure additional notification channels:

1. **Slack**:
   - Set up Slack workspace integration
   - Configure default channels
   - Test Slack notifications

2. **Telegram**:
   - Set up Telegram bot integration
   - Configure bot token and chat ID
   - Test Telegram notifications

3. **Signal**:
   - Set up Signal integration
   - Configure phone number and API key
   - Test Signal notifications

## Backup and Recovery

### Data Backup

Back up your deployment data:

1. **Through Admin Interface**:
   - Navigate to "Admin" > "Backup"
   - Click "Create Backup"
   - Download the backup file

2. **Through Makefile**:
   ```bash
   make backup-instance INSTANCE=team-a
   ```

### Data Restoration

Restore from a backup if needed:

1. **Through Admin Interface**:
   - Navigate to "Admin" > "Backup"
   - Click "Restore from Backup"
   - Upload the backup file

2. **Through Makefile**:
   ```bash
   make restore-instance INSTANCE=team-a BACKUP_FILE=path/to/backup.json
   ```

## Troubleshooting for Administrators

### Common Admin Issues

1. **Matching Not Running**:
   - Check the cron schedule configuration
   - Verify that the scheduler pod is running
   - Check scheduler logs for errors

2. **Email Notifications Not Sending**:
   - Verify AWS SES configuration
   - Check SES sending limits and statistics
   - Review notification service logs

3. **User Authentication Issues**:
   - Check OAuth provider configuration
   - Verify that allowed domains are correctly set
   - Review authentication service logs

### Advanced Troubleshooting

For more complex issues:

1. **Access Pod Logs**:
   ```bash
   kubectl logs -n <instance> deployment/virtual-coffee-api
   ```

2. **Check Database Status**:
   ```bash
   kubectl exec -it -n <instance> deployment/virtual-coffee-api -- python -c "from backend.api.repositories.dynamodb_connection import get_dynamodb_client; print(get_dynamodb_client().list_tables())"
   ```

3. **Test API Endpoints**:
   ```bash
   kubectl port-forward -n <instance> svc/virtual-coffee-api 8000:80
   curl http://localhost:8000/health
   ```

## Best Practices for Administrators

1. **Regular Monitoring**:
   - Check the admin dashboard weekly
   - Review system logs for errors
   - Monitor user feedback and participation rates

2. **Communication**:
   - Send regular updates to users
   - Announce schedule changes in advance
   - Collect and address user feedback

3. **Maintenance**:
   - Keep the platform updated
   - Schedule maintenance during off-hours
   - Test changes in a staging environment first

4. **Documentation**:
   - Document deployment-specific configurations
   - Keep records of customizations and changes
   - Document troubleshooting steps for common issues

5. **Security**:
   - Regularly rotate AWS credentials
   - Review access permissions
   - Monitor for unusual activity

## Getting Help

If you need assistance beyond what's covered in this guide:

1. **Check the Troubleshooting Guide**:
   - Review the [Troubleshooting Guide](troubleshooting-guide.md) for common issues and solutions

2. **Contact Platform Support**:
   - Email [support@example.com](mailto:support@example.com)
   - Include your deployment ID and detailed information about the issue

3. **Open a GitHub Issue**:
   - For bugs or feature requests, open an issue in the GitHub repository
   - Include detailed reproduction steps and environment information
