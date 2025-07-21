"""
Configuration repository implementation for DynamoDB.
"""
import logging
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError
from datetime import datetime

from backend.api.models.config import DeploymentConfig
from backend.api.repositories.base import BaseRepository
from backend.api.repositories.dynamodb_connection import dynamodb_manager

logger = logging.getLogger(__name__)


class ConfigRepository(BaseRepository[DeploymentConfig]):
    """
    Configuration repository implementation for DynamoDB.
    """
    
    def __init__(self):
        """
        Initialize the configuration repository.
        """
        self.table_name = "deployment-configs"
        self.table = dynamodb_manager.get_table(self.table_name)
    
    async def create(self, config: DeploymentConfig) -> DeploymentConfig:
        """
        Create a new deployment configuration.
        
        Args:
            config: The configuration to create
            
        Returns:
            The created configuration
        """
        try:
            # Convert Pydantic model to dict
            config_dict = config.dict()
            
            # Update timestamps
            current_time = datetime.utcnow().isoformat()
            config_dict['created_at'] = current_time
            config_dict['updated_at'] = current_time
            
            # Put item in DynamoDB
            self.table.put_item(Item=config_dict)
            
            return config
        except Exception as e:
            dynamodb_manager.handle_error("create_config", e)
    
    async def get(self, deployment_id: str) -> Optional[DeploymentConfig]:
        """
        Get a deployment configuration by ID.
        
        Args:
            deployment_id: The ID of the deployment
            
        Returns:
            The configuration if found, None otherwise
        """
        try:
            response = self.table.get_item(
                Key={
                    'deployment_id': deployment_id
                }
            )
            
            item = response.get('Item')
            if not item:
                return None
            
            return DeploymentConfig(**item)
        except Exception as e:
            dynamodb_manager.handle_error("get_config", e)
    
    async def get_all(self, filter_params: Optional[Dict[str, Any]] = None) -> List[DeploymentConfig]:
        """
        Get all deployment configurations, optionally filtered.
        
        Args:
            filter_params: Optional filter parameters
            
        Returns:
            A list of configurations
        """
        try:
            # Scan the table
            scan_params = {}
            
            if filter_params:
                filter_expressions = []
                expression_values = {}
                
                for key, value in filter_params.items():
                    filter_expressions.append(f'{key} = :{key}')
                    expression_values[f':{key}'] = value
                
                if filter_expressions:
                    scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
                    scan_params['ExpressionAttributeValues'] = expression_values
            
            response = self.table.scan(**scan_params)
            
            # Convert items to DeploymentConfig objects
            configs = [DeploymentConfig(**item) for item in response.get('Items', [])]
            
            # Handle pagination if needed
            while 'LastEvaluatedKey' in response:
                scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.scan(**scan_params)
                configs.extend([DeploymentConfig(**item) for item in response.get('Items', [])])
            
            return configs
        except Exception as e:
            dynamodb_manager.handle_error("get_all_configs", e)
    
    async def update(self, deployment_id: str, config_update: Dict[str, Any]) -> Optional[DeploymentConfig]:
        """
        Update a deployment configuration.
        
        Args:
            deployment_id: The ID of the deployment to update
            config_update: The fields to update
            
        Returns:
            The updated configuration if found, None otherwise
        """
        try:
            # Get current config to ensure it exists
            current_config = await self.get(deployment_id)
            if not current_config:
                return None
            
            # Update timestamp
            config_update['updated_at'] = datetime.utcnow().isoformat()
            
            # Build update expression
            update_expressions = []
            expression_values = {}
            expression_names = {}
            
            for key, value in config_update.items():
                # Skip deployment_id as it shouldn't be updated
                if key == 'deployment_id':
                    continue
                
                # Handle nested attributes like email_templates
                if key == 'email_templates' and value:
                    for template_key, template_value in value.items():
                        update_expressions.append(f'#email_templates.#{template_key} = :email_templates_{template_key}')
                        expression_names[f'#email_templates'] = 'email_templates'
                        expression_names[f'#{template_key}'] = template_key
                        expression_values[f':email_templates_{template_key}'] = template_value
                else:
                    update_expressions.append(f'#{key} = :{key}')
                    expression_names[f'#{key}'] = key
                    expression_values[f':{key}'] = value
            
            if not update_expressions:
                return current_config  # Nothing to update
            
            # Execute update
            update_expression = 'SET ' + ', '.join(update_expressions)
            
            response = self.table.update_item(
                Key={
                    'deployment_id': deployment_id
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            # Return updated config
            updated_item = response.get('Attributes', {})
            return DeploymentConfig(**updated_item)
        except Exception as e:
            dynamodb_manager.handle_error("update_config", e)
    
    async def delete(self, deployment_id: str) -> bool:
        """
        Delete a deployment configuration.
        
        Args:
            deployment_id: The ID of the deployment to delete
            
        Returns:
            True if the configuration was deleted, False otherwise
        """
        try:
            # Check if config exists
            config = await self.get(deployment_id)
            if not config:
                return False
            
            # Delete the config
            self.table.delete_item(
                Key={
                    'deployment_id': deployment_id
                }
            )
            
            return True
        except Exception as e:
            dynamodb_manager.handle_error("delete_config", e)
            return False