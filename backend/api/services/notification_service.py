"""
Notification service implementation for the Virtual Coffee Platform.

This service handles sending notifications to users about their matches
through various channels, with email as the primary channel for MVP.
"""
import logging
import json
import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Union
from datetime import datetime

from backend.api.models.user import User
from backend.api.models.match import Match
from backend.api.repositories.user_repository import UserRepository
from backend.api.repositories.match_repository import MatchRepository
from backend.api.services.email_templates import get_template, format_participants_html

logger = logging.getLogger(__name__)

# Maximum number of retries for notification attempts
MAX_RETRIES = 3


class NotificationService:
    """
    Notification service for the Virtual Coffee Platform.
    
    This service is responsible for:
    1. Sending match notifications to users
    2. Managing notification channels
    3. Handling retry logic for failed notifications
    4. Supporting multiple notification channels (Phase 2)
    """
    
    def __init__(self, deployment_id: str):
        """
        Initialize the notification service.
        
        Args:
            deployment_id: The deployment ID for multi-tenancy
        """
        self.deployment_id = deployment_id
        self.user_repository = UserRepository(deployment_id)
        self.match_repository = MatchRepository(deployment_id)
        
        # Initialize AWS SES client for email notifications
        self.ses_client = boto3.client('ses')
        
        # Email configuration
        self.sender_email = f"virtual-coffee-{deployment_id}@example.com"  # Replace with actual domain
        
        # Initialize notification channels
        self.channels = self._initialize_notification_channels()
    
    def _initialize_notification_channels(self):
        """
        Initialize notification channels.
        
        In a real implementation, configuration would be loaded from environment variables
        or a configuration service.
        
        Returns:
            Dictionary of notification channel instances
        """
        from backend.api.services.notification_channels import (
            EmailChannel, SlackChannel, TelegramChannel, SignalChannel
        )
        
        # Create channel instances
        email_channel = EmailChannel(self.deployment_id)
        
        # For Phase 2 channels, we would load configuration from environment or config service
        # For now, we'll use placeholder values
        slack_channel = SlackChannel(self.deployment_id)
        telegram_channel = TelegramChannel(self.deployment_id, bot_token="placeholder_token")
        signal_channel = SignalChannel(
            self.deployment_id,
            signal_service_url="https://signal-api.example.com",
            api_key="placeholder_api_key"
        )
        
        return {
            "email": email_channel,
            "slack": slack_channel,
            "telegram": telegram_channel,
            "signal": signal_channel
        }
    
    async def send_match_notification(self, match: Match, retry_count: int = 0) -> bool:
        """
        Send notifications for a match to all participants.
        
        Args:
            match: The match to send notifications for
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            True if all notifications were sent successfully, False otherwise
        """
        try:
            # Get all users in the match
            users = []
            for user_id in match.participants:
                user = await self.user_repository.get(user_id)
                if user:
                    users.append(user)
                else:
                    logger.warning(f"User {user_id} not found for match {match.id}")
            
            if not users:
                logger.error(f"No valid users found for match {match.id}")
                return False
            
            # Send notification to each user
            success = True
            for user in users:
                # Get other participants to include in notification
                other_participants = [u for u in users if u.id != user.id]
                
                # Send notification based on user's preferences
                user_success = await self._send_user_notification(user, match, other_participants)
                success = success and user_success
            
            # Update match notification status if all notifications were sent
            if success:
                match.notification_sent = True
                await self.match_repository.update(match)
                logger.info(f"Successfully sent all notifications for match {match.id}")
            else:
                # Retry if not all notifications were successful
                if retry_count < MAX_RETRIES:
                    logger.info(f"Retrying notifications for match {match.id} (attempt {retry_count + 1}/{MAX_RETRIES})")
                    return await self.send_match_notification(match, retry_count + 1)
                else:
                    logger.error(f"Failed to send all notifications for match {match.id} after {MAX_RETRIES} attempts")
            
            return success
        except Exception as e:
            logger.exception(f"Error sending notifications for match {match.id}: {e}")
            
            # Retry on exception
            if retry_count < MAX_RETRIES:
                logger.info(f"Retrying notifications for match {match.id} (attempt {retry_count + 1}/{MAX_RETRIES})")
                return await self.send_match_notification(match, retry_count + 1)
            
            return False
    
    async def _send_user_notification(self, user: User, match: Match, other_participants: List[User]) -> bool:
        """
        Send a notification to a specific user about their match.
        
        This method tries to send notifications through the user's preferred channels,
        with fallback to email if other channels fail.
        
        Args:
            user: The user to notify
            match: The match information
            other_participants: Other users in the match
            
        Returns:
            True if the notification was sent successfully through any channel, False otherwise
        """
        try:
            # Determine which channels to use based on user preferences
            available_channels = []
            
            # For MVP, we only use email
            # For Phase 2, we check all available channels
            
            # Check if user has notification preferences
            if user.notification_prefs and hasattr(user.notification_prefs, 'primary_channel'):
                primary_channel = user.notification_prefs.primary_channel
                
                # Add primary channel first if available
                if primary_channel in self.channels and self.channels[primary_channel].is_available_for_user(user):
                    available_channels.append(primary_channel)
                
                # Add other enabled channels
                for channel_name, channel in self.channels.items():
                    if channel_name != primary_channel and channel.is_available_for_user(user):
                        available_channels.append(channel_name)
            else:
                # Default to email for MVP
                if 'email' in self.channels and user.email:
                    available_channels.append('email')
            
            # If no channels are available, log error and return
            if not available_channels:
                logger.error(f"No notification channels available for user {user.id}")
                return False
            
            # Try each channel in order until one succeeds
            for channel_name in available_channels:
                channel = self.channels[channel_name]
                try:
                    success = await channel.send_notification(user, match, other_participants)
                    if success:
                        logger.info(f"Successfully sent notification to {user.name} via {channel_name}")
                        return True
                    else:
                        logger.warning(f"Failed to send notification to {user.name} via {channel_name}, trying next channel")
                except Exception as e:
                    logger.warning(f"Error sending notification via {channel_name}: {e}")
                    # Continue to next channel
            
            # If we get here, all channels failed
            logger.error(f"Failed to send notification to {user.name} through any channel")
            return False
        except Exception as e:
            logger.exception(f"Error sending notification to user {user.id}: {e}")
            return False
    
    async def _send_email_notification(self, user: User, match: Match, other_participants: List[User]) -> bool:
        """
        Send an email notification to a user.
        
        Args:
            user: The user to notify
            match: The match information
            other_participants: Other users in the match
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        try:
            # Get email template from the email_templates module
            template = get_template("match_notification")
            if not template:
                logger.error("Match notification email template not found")
                return False
            
            # Format participants HTML using the helper function
            participants_html = format_participants_html(other_participants)
            
            # Get meeting length preference (default to 30 minutes)
            meeting_length = user.preferences.meeting_length if user.preferences and user.preferences.meeting_length else 30
            
            # Base URL for the platform (would be configured in a real implementation)
            platform_url = f"https://virtual-coffee.example.com/{self.deployment_id}"
            preferences_url = f"{platform_url}/preferences"
            
            # Replace template variables
            email_body = template.replace("{{user_name}}", user.name)
            email_body = email_body.replace("{{participants_html}}", participants_html)
            email_body = email_body.replace("{{meeting_length}}", str(meeting_length))
            email_body = email_body.replace("{{platform_url}}", platform_url)
            email_body = email_body.replace("{{preferences_url}}", preferences_url)
            email_body = email_body.replace("{{deployment_id}}", self.deployment_id)
            
            # Create email subject
            subject = f"Virtual Coffee Match - {match.scheduled_date.strftime('%B %d, %Y')}"
            
            # Send email using AWS SES
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={
                    'ToAddresses': [user.email]
                },
                Message={
                    'Subject': {
                        'Data': subject
                    },
                    'Body': {
                        'Html': {
                            'Data': email_body
                        }
                    }
                }
            )
            
            logger.info(f"Sent email notification to {user.email} (Message ID: {response['MessageId']})")
            return True
        except ClientError as e:
            logger.error(f"AWS SES error sending email to {user.email}: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.exception(f"Error sending email to {user.email}: {e}")
            return False
    
    async def send_reminder(self, match: Match) -> bool:
        """
        Send a reminder notification for a match.
        
        Args:
            match: The match to send reminders for
            
        Returns:
            True if all reminders were sent successfully, False otherwise
        """
        # Similar implementation to send_match_notification but using the reminder template
        # For brevity, this is not fully implemented in this example
        logger.info(f"Sending reminders for match {match.id}")
        return True