"""
Match repository implementation for DynamoDB.
"""
import logging
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError
from datetime import datetime

from models.match import Match
from repositories.base import BaseRepository
from repositories.dynamodb_connection import dynamodb_manager

logger = logging.getLogger(__name__)


class MatchRepository(BaseRepository[Match]):
    """
    Match repository implementation for DynamoDB.
    """
    
    def __init__(self, deployment_id: str):
        """
        Initialize the match repository.
        
        Args:
            deployment_id: The deployment ID for multi-tenancy
        """
        self.table_name = f"matches-{deployment_id}"
        self.deployment_id = deployment_id
        self.table = dynamodb_manager.get_table(self.table_name)
    
    async def create(self, match: Match) -> Match:
        """
        Create a new match.
        
        Args:
            match: The match to create
            
        Returns:
            The created match
        """
        try:
            # Ensure deployment_id is set
            match.deployment_id = self.deployment_id
            
            # Convert Pydantic model to dict
            match_dict = match.dict()
            
            # Convert datetime objects to ISO format strings for DynamoDB
            match_dict['scheduled_date'] = match_dict['scheduled_date'].isoformat()
            match_dict['created_at'] = match_dict['created_at'].isoformat()
            
            # Put item in DynamoDB
            self.table.put_item(Item=match_dict)
            
            return match
        except Exception as e:
            dynamodb_manager.handle_error("create_match", e)
    
    async def get(self, id: str) -> Optional[Match]:
        """
        Get a match by ID.
        
        Args:
            id: The ID of the match to get
            
        Returns:
            The match if found, None otherwise
        """
        try:
            response = self.table.get_item(
                Key={
                    'id': id,
                    'deployment_id': self.deployment_id
                }
            )
            
            item = response.get('Item')
            if not item:
                return None
            
            # Convert ISO format strings back to datetime objects
            if 'scheduled_date' in item:
                item['scheduled_date'] = datetime.fromisoformat(item['scheduled_date'])
            if 'created_at' in item:
                item['created_at'] = datetime.fromisoformat(item['created_at'])
            
            return Match(**item)
        except Exception as e:
            dynamodb_manager.handle_error("get_match", e)
    
    async def get_all(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Match]:
        """
        Get all matches, optionally filtered.
        
        Args:
            filter_params: Optional filter parameters
            
        Returns:
            A list of matches
        """
        try:
            # Start with basic query for the deployment
            expression_values = {
                ':deployment_id': self.deployment_id
            }
            
            filter_expression = None
            
            # Add filters if provided
            if filter_params:
                filter_conditions = []
                
                if 'status' in filter_params:
                    filter_conditions.append('status = :status')
                    expression_values[':status'] = filter_params['status']
                
                if 'notification_sent' in filter_params:
                    filter_conditions.append('notification_sent = :notification_sent')
                    expression_values[':notification_sent'] = filter_params['notification_sent']
                
                if 'participant_id' in filter_params:
                    # This requires a more complex filter for array containment
                    filter_conditions.append('contains(participants, :participant_id)')
                    expression_values[':participant_id'] = filter_params['participant_id']
                
                if filter_conditions:
                    filter_expression = ' AND '.join(filter_conditions)
            
            # Query parameters
            query_params = {
                'KeyConditionExpression': 'deployment_id = :deployment_id',
                'ExpressionAttributeValues': expression_values
            }
            
            if filter_expression:
                query_params['FilterExpression'] = filter_expression
            
            # Execute query
            response = self.table.query(**query_params)
            
            # Process items and convert date strings to datetime objects
            matches = []
            for item in response.get('Items', []):
                if 'scheduled_date' in item:
                    item['scheduled_date'] = datetime.fromisoformat(item['scheduled_date'])
                if 'created_at' in item:
                    item['created_at'] = datetime.fromisoformat(item['created_at'])
                
                matches.append(Match(**item))
            
            # Handle pagination if needed
            while 'LastEvaluatedKey' in response:
                query_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.query(**query_params)
                
                for item in response.get('Items', []):
                    if 'scheduled_date' in item:
                        item['scheduled_date'] = datetime.fromisoformat(item['scheduled_date'])
                    if 'created_at' in item:
                        item['created_at'] = datetime.fromisoformat(item['created_at'])
                    
                    matches.append(Match(**item))
            
            return matches
        except Exception as e:
            dynamodb_manager.handle_error("get_all_matches", e)
    
    async def get_matches_for_user(self, user_id: str) -> List[Match]:
        """
        Get all matches for a specific user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            A list of matches
        """
        return await self.get_all({'participant_id': user_id})
    
    async def update(self, id: str, match_update: Dict[str, Any]) -> Optional[Match]:
        """
        Update a match.
        
        Args:
            id: The ID of the match to update
            match_update: The fields to update
            
        Returns:
            The updated match if found, None otherwise
        """
        try:
            # Get current match to ensure it exists
            current_match = await self.get(id)
            if not current_match:
                return None
            
            # Build update expression
            update_expressions = []
            expression_values = {}
            expression_names = {}
            
            for key, value in match_update.items():
                # Skip id and deployment_id as they shouldn't be updated
                if key in ['id', 'deployment_id']:
                    continue
                
                # Handle datetime objects
                if key == 'scheduled_date' and value:
                    update_expressions.append(f'#{key} = :{key}')
                    expression_names[f'#{key}'] = key
                    expression_values[f':{key}'] = value.isoformat()
                else:
                    update_expressions.append(f'#{key} = :{key}')
                    expression_names[f'#{key}'] = key
                    expression_values[f':{key}'] = value
            
            if not update_expressions:
                return current_match  # Nothing to update
            
            # Execute update
            update_expression = 'SET ' + ', '.join(update_expressions)
            
            response = self.table.update_item(
                Key={
                    'id': id,
                    'deployment_id': self.deployment_id
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            # Return updated match
            updated_item = response.get('Attributes', {})
            
            # Convert ISO format strings back to datetime objects
            if 'scheduled_date' in updated_item:
                updated_item['scheduled_date'] = datetime.fromisoformat(updated_item['scheduled_date'])
            if 'created_at' in updated_item:
                updated_item['created_at'] = datetime.fromisoformat(updated_item['created_at'])
            
            return Match(**updated_item)
        except Exception as e:
            dynamodb_manager.handle_error("update_match", e)
    
    async def delete(self, id: str) -> bool:
        """
        Delete a match.
        
        Args:
            id: The ID of the match to delete
            
        Returns:
            True if the match was deleted, False otherwise
        """
        try:
            # Check if match exists
            match = await self.get(id)
            if not match:
                return False
            
            # Delete the match
            self.table.delete_item(
                Key={
                    'id': id,
                    'deployment_id': self.deployment_id
                }
            )
            
            return True
        except Exception as e:
            dynamodb_manager.handle_error("delete_match", e)
            return False