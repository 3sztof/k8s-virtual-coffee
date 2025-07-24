"""
DynamoDB connection manager.
"""
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDBConnectionManager:
    """
    Manages DynamoDB connections and provides error handling.
    """

    _instance = None
    _client = None
    _resource = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DynamoDBConnectionManager, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance

    def _initialize_connection(self):
        """Initialize the DynamoDB connection."""
        try:
            # Get configuration from environment variables with fallbacks
            region = os.environ.get("AWS_REGION", "us-east-1")
            endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL")

            # Connection parameters
            conn_params = {
                "region_name": region,
            }

            # For local development or testing, use a local DynamoDB endpoint
            if endpoint_url:
                conn_params["endpoint_url"] = endpoint_url
                logger.info(f"Using custom DynamoDB endpoint: {endpoint_url}")

            # Create the client and resource
            self._client = boto3.client("dynamodb", **conn_params)
            self._resource = boto3.resource("dynamodb", **conn_params)

            logger.info(f"DynamoDB connection initialized in region {region}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB connection: {e!s}")
            raise

    @property
    def client(self):
        """Get the DynamoDB client."""
        return self._client

    @property
    def resource(self):
        """Get the DynamoDB resource."""
        return self._resource

    def get_table(self, table_name: str):
        """
        Get a DynamoDB table.

        Args:
            table_name: The name of the table

        Returns:
            The DynamoDB table resource
        """
        return self._resource.Table(table_name)

    def handle_error(self, operation: str, error: Exception) -> None:
        """
        Handle DynamoDB errors.

        Args:
            operation: The operation being performed
            error: The error that occurred

        Raises:
            Exception: The appropriate exception based on the error
        """
        if isinstance(error, ClientError):
            error_code = error.response.get("Error", {}).get("Code")
            error_message = error.response.get("Error", {}).get("Message")

            logger.error(f"DynamoDB {operation} error: {error_code} - {error_message}")

            if error_code == "ResourceNotFoundException":
                raise ValueError(f"Table not found: {error_message}")
            elif error_code == "ConditionalCheckFailedException":
                raise ValueError(f"Condition check failed: {error_message}")
            elif error_code == "ProvisionedThroughputExceededException":
                raise RuntimeError(f"Throughput exceeded: {error_message}")
            elif error_code == "ValidationException":
                raise ValueError(f"Validation error: {error_message}")
            else:
                raise RuntimeError(f"DynamoDB error: {error_code} - {error_message}")
        else:
            logger.error(f"Unexpected error during {operation}: {error!s}")
            raise error


# Singleton instance
dynamodb_manager = DynamoDBConnectionManager()
