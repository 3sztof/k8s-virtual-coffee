"""
User repository implementation for DynamoDB.
"""
import logging
from datetime import datetime
from typing import Any, Optional

from models.user import User
from repositories.base import BaseRepository
from repositories.dynamodb_connection import dynamodb_manager

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """
    User repository implementation for DynamoDB.
    """

    def __init__(self, deployment_id: str):
        """
        Initialize the user repository.

        Args:
            deployment_id: The deployment ID for multi-tenancy
        """
        self.table_name = f"users-{deployment_id}"
        self.deployment_id = deployment_id
        self.table = dynamodb_manager.get_table(self.table_name)

    async def create(self, user: User) -> User:
        """
        Create a new user.

        Args:
            user: The user to create

        Returns:
            The created user
        """
        try:
            # Ensure deployment_id is set
            user.deployment_id = self.deployment_id

            # Convert Pydantic model to dict
            user_dict = user.dict()

            # Update timestamps
            current_time = datetime.utcnow().isoformat()
            user_dict["created_at"] = current_time
            user_dict["updated_at"] = current_time

            # Put item in DynamoDB
            self.table.put_item(Item=user_dict)

            return user
        except Exception as e:
            dynamodb_manager.handle_error("create_user", e)

    async def get(self, id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            id: The ID of the user to get

        Returns:
            The user if found, None otherwise
        """
        try:
            response = self.table.get_item(
                Key={
                    "id": id,
                    "deployment_id": self.deployment_id,
                },
            )

            item = response.get("Item")
            if not item:
                return None

            return User(**item)
        except Exception as e:
            dynamodb_manager.handle_error("get_user", e)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.

        Args:
            email: The email of the user to get

        Returns:
            The user if found, None otherwise
        """
        try:
            # Use a GSI for email lookups
            response = self.table.query(
                IndexName="email-index",
                KeyConditionExpression="email = :email AND deployment_id = :deployment_id",
                ExpressionAttributeValues={
                    ":email": email,
                    ":deployment_id": self.deployment_id,
                },
            )

            items = response.get("Items", [])
            if not items:
                return None

            return User(**items[0])
        except Exception as e:
            dynamodb_manager.handle_error("get_user_by_email", e)

    async def get_all(
        self, filter_params: Optional[dict[str, Any]] = None
    ) -> list[User]:
        """
        Get all users, optionally filtered.

        Args:
            filter_params: Optional filter parameters

        Returns:
            A list of users
        """
        try:
            # Start with basic query for the deployment
            expression_values = {
                ":deployment_id": self.deployment_id,
            }

            filter_expression = None

            # Add filters if provided
            if filter_params:
                filter_conditions = []

                if "is_active" in filter_params:
                    filter_conditions.append("is_active = :is_active")
                    expression_values[":is_active"] = filter_params["is_active"]

                if "is_paused" in filter_params:
                    filter_conditions.append("is_paused = :is_paused")
                    expression_values[":is_paused"] = filter_params["is_paused"]

                if filter_conditions:
                    filter_expression = " AND ".join(filter_conditions)

            # Query parameters
            query_params = {
                "KeyConditionExpression": "deployment_id = :deployment_id",
                "ExpressionAttributeValues": expression_values,
            }

            if filter_expression:
                query_params["FilterExpression"] = filter_expression

            # Execute query
            response = self.table.query(**query_params)

            # Convert items to User objects
            users = [User(**item) for item in response.get("Items", [])]

            # Handle pagination if needed
            while "LastEvaluatedKey" in response:
                query_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]
                response = self.table.query(**query_params)
                users.extend([User(**item) for item in response.get("Items", [])])

            return users
        except Exception as e:
            dynamodb_manager.handle_error("get_all_users", e)

    async def update(self, id: str, user_update: dict[str, Any]) -> Optional[User]:
        """
        Update a user.

        Args:
            id: The ID of the user to update
            user_update: The fields to update

        Returns:
            The updated user if found, None otherwise
        """
        try:
            # Get current user to ensure it exists
            current_user = await self.get(id)
            if not current_user:
                return None

            # Update timestamp
            user_update["updated_at"] = datetime.utcnow().isoformat()

            # Build update expression
            update_expressions = []
            expression_values = {}
            expression_names = {}

            for key, value in user_update.items():
                # Skip id and deployment_id as they shouldn't be updated
                if key in ["id", "deployment_id"]:
                    continue

                # Handle nested attributes like preferences
                if key == "preferences" and value:
                    for pref_key, pref_value in value.items():
                        update_expressions.append(
                            f"#preferences.#{pref_key} = :preferences_{pref_key}"
                        )
                        expression_names["#preferences"] = "preferences"
                        expression_names[f"#{pref_key}"] = pref_key
                        expression_values[f":preferences_{pref_key}"] = pref_value
                else:
                    update_expressions.append(f"#{key} = :{key}")
                    expression_names[f"#{key}"] = key
                    expression_values[f":{key}"] = value

            if not update_expressions:
                return current_user  # Nothing to update

            # Execute update
            update_expression = "SET " + ", ".join(update_expressions)

            response = self.table.update_item(
                Key={
                    "id": id,
                    "deployment_id": self.deployment_id,
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW",
            )

            # Return updated user
            updated_item = response.get("Attributes", {})
            return User(**updated_item)
        except Exception as e:
            dynamodb_manager.handle_error("update_user", e)

    async def delete(self, id: str) -> bool:
        """
        Delete a user.

        Args:
            id: The ID of the user to delete

        Returns:
            True if the user was deleted, False otherwise
        """
        try:
            # Check if user exists
            user = await self.get(id)
            if not user:
                return False

            # Delete the user
            self.table.delete_item(
                Key={
                    "id": id,
                    "deployment_id": self.deployment_id,
                },
            )

            return True
        except Exception as e:
            dynamodb_manager.handle_error("delete_user", e)
            return False
