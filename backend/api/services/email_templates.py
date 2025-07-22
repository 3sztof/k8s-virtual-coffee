"""
Email templates for the Virtual Coffee Platform.

This module contains HTML templates for various email notifications.
"""

# Match notification template
MATCH_NOTIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtual Coffee Match</title>
    <style>
        body {
            font-family: 'Amazon Ember', Arial, sans-serif;
            line-height: 1.6;
            color: #16191f;
            margin: 0;
            padding: 0;
            background-color: #f8f8f8;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border: 1px solid #eaeded;
            border-radius: 4px;
            overflow: hidden;
        }
        .header {
            background-color: #232f3e;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            color: #ffffff;
            margin: 0;
            font-size: 24px;
            font-weight: 500;
        }
        .content {
            padding: 30px;
        }
        .match-details {
            background-color: #f2f3f3;
            border-radius: 4px;
            padding: 20px;
            margin: 20px 0;
        }
        .participant {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eaeded;
        }
        .participant:last-child {
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }
        .button {
            display: inline-block;
            background-color: #ff9900;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 4px;
            margin-top: 20px;
        }
        .footer {
            background-color: #f2f3f3;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #687078;
        }
        .preferences-link {
            color: #0073bb;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Virtual Coffee Match</h1>
        </div>
        <div class="content">
            <p>Hello {{user_name}},</p>
            <p>You've been matched for a virtual coffee meeting! This is a great opportunity to connect with colleagues and share ideas in a casual setting.</p>
            
            <div class="match-details">
                <h2>Your Match Details</h2>
                {{participants_html}}
                
                <p>We recommend scheduling a {{meeting_length}} minute meeting at a time that works for everyone.</p>
            </div>
            
            <p>Some conversation starters:</p>
            <ul>
                <li>What are you working on currently?</li>
                <li>What's something interesting you've learned recently?</li>
                <li>Any book/podcast recommendations?</li>
            </ul>
            
            <p>Enjoy your virtual coffee!</p>
            
            <a href="{{platform_url}}" class="button">View Match in Platform</a>
        </div>
        <div class="footer">
            <p>This is an automated message from the Virtual Coffee Platform.</p>
            <p>If you wish to pause your participation, please <a href="{{preferences_url}}" class="preferences-link">update your preferences</a>.</p>
            <p>Deployment: {{deployment_id}}</p>
        </div>
    </div>
</body>
</html>
"""

# Match reminder template
MATCH_REMINDER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtual Coffee Reminder</title>
    <style>
        body {
            font-family: 'Amazon Ember', Arial, sans-serif;
            line-height: 1.6;
            color: #16191f;
            margin: 0;
            padding: 0;
            background-color: #f8f8f8;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border: 1px solid #eaeded;
            border-radius: 4px;
            overflow: hidden;
        }
        .header {
            background-color: #232f3e;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            color: #ffffff;
            margin: 0;
            font-size: 24px;
            font-weight: 500;
        }
        .content {
            padding: 30px;
        }
        .match-details {
            background-color: #f2f3f3;
            border-radius: 4px;
            padding: 20px;
            margin: 20px 0;
        }
        .button {
            display: inline-block;
            background-color: #ff9900;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 4px;
            margin-top: 20px;
        }
        .footer {
            background-color: #f2f3f3;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #687078;
        }
        .preferences-link {
            color: #0073bb;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Virtual Coffee Reminder</h1>
        </div>
        <div class="content">
            <p>Hello {{user_name}},</p>
            <p>This is a friendly reminder about your virtual coffee match. Have you scheduled your meeting yet?</p>
            
            <div class="match-details">
                <h2>Your Match Details</h2>
                {{participants_html}}
            </div>
            
            <p>Don't miss out on this opportunity to connect with your colleagues!</p>
            
            <a href="{{platform_url}}" class="button">View Match in Platform</a>
        </div>
        <div class="footer">
            <p>This is an automated message from the Virtual Coffee Platform.</p>
            <p>If you wish to pause your participation, please <a href="{{preferences_url}}" class="preferences-link">update your preferences</a>.</p>
            <p>Deployment: {{deployment_id}}</p>
        </div>
    </div>
</body>
</html>
"""

# Weekly summary template
WEEKLY_SUMMARY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtual Coffee Weekly Summary</title>
    <style>
        body {
            font-family: 'Amazon Ember', Arial, sans-serif;
            line-height: 1.6;
            color: #16191f;
            margin: 0;
            padding: 0;
            background-color: #f8f8f8;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border: 1px solid #eaeded;
            border-radius: 4px;
            overflow: hidden;
        }
        .header {
            background-color: #232f3e;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            color: #ffffff;
            margin: 0;
            font-size: 24px;
            font-weight: 500;
        }
        .content {
            padding: 30px;
        }
        .stats {
            background-color: #f2f3f3;
            border-radius: 4px;
            padding: 20px;
            margin: 20px 0;
        }
        .stat-item {
            margin-bottom: 10px;
        }
        .button {
            display: inline-block;
            background-color: #ff9900;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 4px;
            margin-top: 20px;
        }
        .footer {
            background-color: #f2f3f3;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #687078;
        }
        .preferences-link {
            color: #0073bb;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Virtual Coffee Weekly Summary</h1>
        </div>
        <div class="content">
            <p>Hello {{user_name}},</p>
            <p>Here's your weekly summary of virtual coffee activity:</p>
            
            <div class="stats">
                <h2>This Week's Stats</h2>
                <div class="stat-item"><strong>Matches Created:</strong> {{matches_count}}</div>
                <div class="stat-item"><strong>Active Participants:</strong> {{active_participants}}</div>
                <div class="stat-item"><strong>Your Status:</strong> {{user_status}}</div>
            </div>
            
            <p>{{custom_message}}</p>
            
            <a href="{{platform_url}}" class="button">Visit Platform</a>
        </div>
        <div class="footer">
            <p>This is an automated message from the Virtual Coffee Platform.</p>
            <p>If you wish to pause your participation, please <a href="{{preferences_url}}" class="preferences-link">update your preferences</a>.</p>
            <p>Deployment: {{deployment_id}}</p>
        </div>
    </div>
</body>
</html>
"""


def get_template(template_name):
    """
    Get an email template by name.
    
    Args:
        template_name: The name of the template to retrieve
        
    Returns:
        The template string or None if not found
    """
    templates = {
        "match_notification": MATCH_NOTIFICATION_TEMPLATE,
        "match_reminder": MATCH_REMINDER_TEMPLATE,
        "weekly_summary": WEEKLY_SUMMARY_TEMPLATE
    }
    
    return templates.get(template_name)


def format_participants_html(participants):
    """
    Format a list of participants into HTML.
    
    Args:
        participants: List of User objects
        
    Returns:
        HTML string with participant information
    """
    html = ""
    for participant in participants:
        html += f"""
        <div class="participant">
            <strong>Name:</strong> {participant.name}<br>
            <strong>Email:</strong> <a href="mailto:{participant.email}">{participant.email}</a>
        </div>
        """
    return html