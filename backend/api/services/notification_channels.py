"""
Notification channel implementations for the Virtual Coffee Platform.

This module provides interfaces and implementations for different notification channels
such as email, Slack, Telegram, and Signal.
"""
import logging
from abc import ABC, abstractmethod

import boto3
import requests
from botocore.exceptions import ClientError

from backend.api.models.match import Match
from backend.api.models.user import User
from backend.api.services.email_templates import format_participants_html, get_template

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send_notification(
        self, user: User, match: Match, other_participants: list[User]
    ) -> bool:
        """
        Send a notification to a user.

        Args:
            user: The user to notify
            match: The match information
            other_participants: Other users in the match

        Returns:
            True if the notification was sent successfully, False otherwise
        """

    @abstractmethod
    def is_available_for_user(self, user: User) -> bool:
        """
        Check if this channel is available for the user.

        Args:
            user: The user to check

        Returns:
            True if the channel is available, False otherwise
        """


class EmailChannel(NotificationChannel):
    """Email notification channel using AWS SES."""

    def __init__(self, deployment_id: str):
        """
        Initialize the email channel.

        Args:
            deployment_id: The deployment ID for multi-tenancy
        """
        self.deployment_id = deployment_id
        self.ses_client = boto3.client("ses")
        self.sender_email = (
            f"virtual-coffee-{deployment_id}@example.com"
        )  # Replace with actual domain

    async def send_notification(
        self, user: User, match: Match, other_participants: list[User]
    ) -> bool:
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
            # Check if user has an email
            if not user.email:
                logger.error(f"User {user.id} has no email address")
                return False

            # Get email template
            template = get_template("match_notification")
            if not template:
                logger.error("Match notification email template not found")
                return False

            # Format participants HTML
            participants_html = format_participants_html(other_participants)

            # Get meeting length preference (default to 30 minutes)
            meeting_length = (
                user.preferences.meeting_length
                if user.preferences and user.preferences.meeting_length
                else 30
            )

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
            subject = (
                f"Virtual Coffee Match - {match.scheduled_date.strftime('%B %d, %Y')}"
            )

            # Send email using AWS SES
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={
                    "ToAddresses": [user.email],
                },
                Message={
                    "Subject": {
                        "Data": subject,
                    },
                    "Body": {
                        "Html": {
                            "Data": email_body,
                        },
                    },
                },
            )

            logger.info(
                f"Sent email notification to {user.email} (Message ID: {response['MessageId']})"
            )
            return True
        except ClientError as e:
            logger.error(
                f"AWS SES error sending email to {user.email}: {e.response['Error']['Message']}"
            )
            return False
        except Exception as e:
            logger.exception(f"Error sending email to {user.email}: {e}")
            return False

    def is_available_for_user(self, user: User) -> bool:
        """
        Check if email notifications are available for the user.

        Args:
            user: The user to check

        Returns:
            True if email notifications are available, False otherwise
        """
        # Check if user has an email address and has enabled email notifications
        if not user.email:
            return False

        if not user.notification_prefs:
            return True  # Default to email if no preferences are set

        return user.notification_prefs.email


class SlackChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, deployment_id: str):
        """
        Initialize the Slack channel.

        Args:
            deployment_id: The deployment ID for multi-tenancy
        """
        self.deployment_id = deployment_id

    async def send_notification(
        self, user: User, match: Match, other_participants: list[User]
    ) -> bool:
        """
        Send a Slack notification to a user.

        Args:
            user: The user to notify
            match: The match information
            other_participants: Other users in the match

        Returns:
            True if the notification was sent successfully, False otherwise
        """
        try:
            # Check if user has a Slack webhook
            if not user.notification_prefs or not user.notification_prefs.slack_webhook:
                logger.error(f"User {user.id} has no Slack webhook configured")
                return False

            # Create message text
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "Virtual Coffee Match",
                            "emoji": True,
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Hello {user.name},\n\nYou've been matched for a virtual coffee meeting!",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Your match details:*",
                        },
                    },
                ],
            }

            # Add participant blocks
            for participant in other_participants:
                message["blocks"].append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Name:* {participant.name}\n*Email:* {participant.email}",
                        },
                    }
                )

            # Add meeting length recommendation
            meeting_length = (
                user.preferences.meeting_length
                if user.preferences and user.preferences.meeting_length
                else 30
            )
            message["blocks"].append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"We recommend scheduling a {meeting_length} minute meeting at a time that works for everyone.",
                    },
                }
            )

            # Add platform link
            platform_url = f"https://virtual-coffee.example.com/{self.deployment_id}"
            message["blocks"].append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Match in Platform",
                                "emoji": True,
                            },
                            "url": platform_url,
                        },
                    ],
                }
            )

            # Send message to Slack webhook
            response = requests.post(
                user.notification_prefs.slack_webhook,
                json=message,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                logger.info(f"Sent Slack notification to {user.name}")
                return True
            else:
                logger.error(
                    f"Failed to send Slack notification: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.exception(f"Error sending Slack notification to {user.name}: {e}")
            return False

    def is_available_for_user(self, user: User) -> bool:
        """
        Check if Slack notifications are available for the user.

        Args:
            user: The user to check

        Returns:
            True if Slack notifications are available, False otherwise
        """
        return (
            user.notification_prefs
            and user.notification_prefs.slack
            and user.notification_prefs.slack_webhook
        )


class TelegramChannel(NotificationChannel):
    """Telegram notification channel."""

    def __init__(self, deployment_id: str, bot_token: str):
        """
        Initialize the Telegram channel.

        Args:
            deployment_id: The deployment ID for multi-tenancy
            bot_token: The Telegram bot token
        """
        self.deployment_id = deployment_id
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_notification(
        self, user: User, match: Match, other_participants: list[User]
    ) -> bool:
        """
        Send a Telegram notification to a user.

        Args:
            user: The user to notify
            match: The match information
            other_participants: Other users in the match

        Returns:
            True if the notification was sent successfully, False otherwise
        """
        try:
            # Check if user has a Telegram chat ID
            if (
                not user.notification_prefs
                or not user.notification_prefs.telegram_chat_id
            ):
                logger.error(f"User {user.id} has no Telegram chat ID configured")
                return False

            # Create message text
            message_text = "*Virtual Coffee Match*\n\n"
            message_text += f"Hello {user.name},\n\n"
            message_text += "You've been matched for a virtual coffee meeting!\n\n"
            message_text += "*Your match details:*\n"

            for participant in other_participants:
                message_text += f"*Name:* {participant.name}\n"
                message_text += f"*Email:* {participant.email}\n\n"

            # Add meeting length recommendation
            meeting_length = (
                user.preferences.meeting_length
                if user.preferences and user.preferences.meeting_length
                else 30
            )
            message_text += f"We recommend scheduling a {meeting_length} minute meeting at a time that works for everyone.\n\n"

            # Add platform link
            platform_url = f"https://virtual-coffee.example.com/{self.deployment_id}"
            message_text += f"[View Match in Platform]({platform_url})"

            # Send message to Telegram
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": user.notification_prefs.telegram_chat_id,
                    "text": message_text,
                    "parse_mode": "Markdown",
                },
            )

            if response.status_code == 200:
                logger.info(f"Sent Telegram notification to {user.name}")
                return True
            else:
                logger.error(
                    f"Failed to send Telegram notification: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.exception(f"Error sending Telegram notification to {user.name}: {e}")
            return False

    def is_available_for_user(self, user: User) -> bool:
        """
        Check if Telegram notifications are available for the user.

        Args:
            user: The user to check

        Returns:
            True if Telegram notifications are available, False otherwise
        """
        return (
            user.notification_prefs
            and user.notification_prefs.telegram
            and user.notification_prefs.telegram_chat_id
        )


class SignalChannel(NotificationChannel):
    """Signal notification channel."""

    def __init__(self, deployment_id: str, signal_service_url: str, api_key: str):
        """
        Initialize the Signal channel.

        Args:
            deployment_id: The deployment ID for multi-tenancy
            signal_service_url: URL of the Signal API service
            api_key: API key for the Signal service
        """
        self.deployment_id = deployment_id
        self.signal_service_url = signal_service_url
        self.api_key = api_key

    async def send_notification(
        self, user: User, match: Match, other_participants: list[User]
    ) -> bool:
        """
        Send a Signal notification to a user.

        Args:
            user: The user to notify
            match: The match information
            other_participants: Other users in the match

        Returns:
            True if the notification was sent successfully, False otherwise
        """
        try:
            # Check if user has a Signal number
            if not user.notification_prefs or not user.notification_prefs.signal_number:
                logger.error(f"User {user.id} has no Signal number configured")
                return False

            # Create message text
            message_text = "Virtual Coffee Match\n\n"
            message_text += f"Hello {user.name},\n\n"
            message_text += "You've been matched for a virtual coffee meeting!\n\n"
            message_text += "Your match details:\n"

            for participant in other_participants:
                message_text += f"Name: {participant.name}\n"
                message_text += f"Email: {participant.email}\n\n"

            # Add meeting length recommendation
            meeting_length = (
                user.preferences.meeting_length
                if user.preferences and user.preferences.meeting_length
                else 30
            )
            message_text += f"We recommend scheduling a {meeting_length} minute meeting at a time that works for everyone.\n\n"

            # Add platform link
            platform_url = f"https://virtual-coffee.example.com/{self.deployment_id}"
            message_text += f"View Match in Platform: {platform_url}"

            # Send message to Signal
            # Note: This is a placeholder implementation as Signal doesn't have an official API
            # In a real implementation, this would use a Signal API service or integration
            response = requests.post(
                f"{self.signal_service_url}/send",
                json={
                    "number": user.notification_prefs.signal_number,
                    "message": message_text,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )

            if response.status_code == 200:
                logger.info(f"Sent Signal notification to {user.name}")
                return True
            else:
                logger.error(
                    f"Failed to send Signal notification: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.exception(f"Error sending Signal notification to {user.name}: {e}")
            return False

    def is_available_for_user(self, user: User) -> bool:
        """
        Check if Signal notifications are available for the user.

        Args:
            user: The user to check

        Returns:
            True if Signal notifications are available, False otherwise
        """
        return (
            user.notification_prefs
            and user.notification_prefs.signal
            and user.notification_prefs.signal_number
        )
