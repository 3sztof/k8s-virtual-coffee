"""
Script to send notifications for matches.

This script is executed by the ArgoCD Workflow after matching to notify
participants about their matches.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

from backend.api.models.match import Match
from backend.api.repositories.match_repository import MatchRepository
from backend.api.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


async def send_notifications():
    """
    Send notifications for recent matches.
    
    This function:
    1. Gets the deployment ID from environment variables
    2. Retrieves recent matches that haven't been notified
    3. Uses the NotificationService to send notifications to all participants
    4. Updates the match records to mark notifications as sent
    
    Returns:
        0 if successful, 1 if an error occurred
    """
    # Get deployment ID from environment
    deployment_id = os.environ.get("DEPLOYMENT_ID")
    if not deployment_id:
        logger.error("No deployment ID provided")
        return 1
    
    logger.info(f"Sending notifications for deployment {deployment_id}")
    
    try:
        # Create repositories and services
        match_repository = MatchRepository(deployment_id)
        notification_service = NotificationService(deployment_id)
        
        # Get all matches
        all_matches = await match_repository.get_all()
        
        # Filter to matches that need notifications
        pending_matches = [
            match for match in all_matches
            if not match.notification_sent
        ]
        
        if not pending_matches:
            logger.info(f"No pending notifications for deployment {deployment_id}")
            return 0
        
        logger.info(f"Found {len(pending_matches)} matches requiring notifications")
        
        # Process each match
        success_count = 0
        failure_count = 0
        
        for match in pending_matches:
            success = await notification_service.send_match_notification(match)
            if success:
                logger.info(f"Successfully sent notifications for match {match.id}")
                success_count += 1
            else:
                logger.error(f"Failed to send notifications for match {match.id}")
                failure_count += 1
        
        logger.info(f"Notification summary: {success_count} successful, {failure_count} failed")
        
        # Return success if at least some notifications were sent
        return 0 if success_count > 0 else 1
    except Exception as e:
        logger.exception(f"Error sending notifications for deployment {deployment_id}")
        return 1


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the notification function
    exit_code = asyncio.run(send_notifications())
    
    # Exit with the appropriate code
    sys.exit(exit_code)