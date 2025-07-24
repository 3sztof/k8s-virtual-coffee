"""
Script to run the matching algorithm.

This script is executed by the Kubernetes CronJob to create matches
for a specific deployment.
"""
import asyncio
import logging
import os
import sys

from backend.api.services.matching_service import MatchingService

logger = logging.getLogger(__name__)


async def run_matching():
    """
    Run the matching algorithm for a deployment.

    This function:
    1. Gets the deployment ID from environment variables
    2. Creates a matching service for the deployment
    3. Runs the matching algorithm
    4. Logs the results

    Returns:
        0 if successful, 1 if an error occurred
    """
    # Get deployment ID from environment
    deployment_id = os.environ.get("DEPLOYMENT_ID")
    if not deployment_id:
        logger.error("No deployment ID provided")
        return 1

    logger.info(f"Running matching for deployment {deployment_id}")

    try:
        # Create matching service
        matching_service = MatchingService(deployment_id)

        # Run matching algorithm
        matches = await matching_service.create_matches()

        # Log results
        logger.info(f"Created {len(matches)} matches for deployment {deployment_id}")

        return 0
    except Exception as e:
        logger.exception(f"Error running matching for deployment {deployment_id}: {e}")
        return 1


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the matching function
    exit_code = asyncio.run(run_matching())

    # Exit with the appropriate code
    sys.exit(exit_code)
