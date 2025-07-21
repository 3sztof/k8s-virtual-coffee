"""
Tests for repository implementations.
"""
import pytest
import boto3
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

from models.user import User, Preferences
from models.match import Match
from repositories.user_repository import UserRepository
from repositories.match_repository import MatchRepository
from repositories.dynamodb_connection import DynamoDBConnectionManager


# Mock DynamoDB for testing
@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB for testing."""
    with patch('repositories.dynamodb_connection.boto3') as mock_boto3:
        # Mock the DynamoDB client and resource
        mock_client = MagicMock()
        mock_resource = MagicMock()
        mock_table = MagicMock()
        
        # Configure the mocks
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = mock_resource
        mock_resource.Table.return_value = mock_table
        
        # Reset the singleton instance
        DynamoDBConnectionManager._instance = None
        
        yield {
            'client': mock_client,
            'resource': mock_resource,
            'table': mock_table
        }


class TestUserRepository:
    """Tests for UserRepository."""
    
    @pytest.fixture
    def user_repo(self, mock_dynamodb):
        """Create a UserRepository instance with mocked DynamoDB."""
        return UserRepository('test-deployment')
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        preferences = Preferences(
            availability=["Monday 9-10", "Wednesday 14-15"],
            topics=["Technology", "Coffee"],
            meeting_length=30
        )
        
        return User(
            id="test-user-id",
            email="test@example.com",
            name="Test User",
            deployment_id="test-deployment",
            preferences=preferences
        )
    
    async def test_create_user(self, user_repo, sample_user, mock_dynamodb):
        """Test creating a user."""
        # Configure the mock
        mock_dynamodb['table'].put_item.return_value = {}
        
        # Call the method
        result = await user_repo.create(sample_user)
        
        # Verify the result
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.name == sample_user.name
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].put_item.assert_called_once()
        call_args = mock_dynamodb['table'].put_item.call_args[1]
        assert 'Item' in call_args
        assert call_args['Item']['id'] == sample_user.id
        assert call_args['Item']['email'] == sample_user.email
    
    async def test_get_user(self, user_repo, sample_user, mock_dynamodb):
        """Test getting a user by ID."""
        # Configure the mock
        mock_dynamodb['table'].get_item.return_value = {
            'Item': sample_user.dict()
        }
        
        # Call the method
        result = await user_repo.get(sample_user.id)
        
        # Verify the result
        assert result is not None
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].get_item.assert_called_once_with(
            Key={
                'id': sample_user.id,
                'deployment_id': 'test-deployment'
            }
        )
    
    async def test_get_user_not_found(self, user_repo, mock_dynamodb):
        """Test getting a non-existent user."""
        # Configure the mock
        mock_dynamodb['table'].get_item.return_value = {}
        
        # Call the method
        result = await user_repo.get('non-existent-id')
        
        # Verify the result
        assert result is None
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].get_item.assert_called_once()
    
    async def test_get_all_users(self, user_repo, sample_user, mock_dynamodb):
        """Test getting all users."""
        # Configure the mock
        mock_dynamodb['table'].query.return_value = {
            'Items': [sample_user.dict()]
        }
        
        # Call the method
        result = await user_repo.get_all()
        
        # Verify the result
        assert len(result) == 1
        assert result[0].id == sample_user.id
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].query.assert_called_once()
        call_args = mock_dynamodb['table'].query.call_args[1]
        assert 'KeyConditionExpression' in call_args
        assert call_args['KeyConditionExpression'] == 'deployment_id = :deployment_id'
    
    async def test_get_all_users_with_filter(self, user_repo, sample_user, mock_dynamodb):
        """Test getting users with filter."""
        # Configure the mock
        mock_dynamodb['table'].query.return_value = {
            'Items': [sample_user.dict()]
        }
        
        # Call the method with filter
        result = await user_repo.get_all({'is_active': True})
        
        # Verify the result
        assert len(result) == 1
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].query.assert_called_once()
        call_args = mock_dynamodb['table'].query.call_args[1]
        assert 'FilterExpression' in call_args
        assert call_args['FilterExpression'] == 'is_active = :is_active'
    
    async def test_update_user(self, user_repo, sample_user, mock_dynamodb):
        """Test updating a user."""
        # Configure the mocks
        mock_dynamodb['table'].get_item.return_value = {
            'Item': sample_user.dict()
        }
        
        mock_dynamodb['table'].update_item.return_value = {
            'Attributes': {
                **sample_user.dict(),
                'name': 'Updated Name'
            }
        }
        
        # Call the method
        result = await user_repo.update(sample_user.id, {'name': 'Updated Name'})
        
        # Verify the result
        assert result is not None
        assert result.name == 'Updated Name'
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].update_item.assert_called_once()
    
    async def test_delete_user(self, user_repo, sample_user, mock_dynamodb):
        """Test deleting a user."""
        # Configure the mocks
        mock_dynamodb['table'].get_item.return_value = {
            'Item': sample_user.dict()
        }
        
        mock_dynamodb['table'].delete_item.return_value = {}
        
        # Call the method
        result = await user_repo.delete(sample_user.id)
        
        # Verify the result
        assert result is True
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].delete_item.assert_called_once_with(
            Key={
                'id': sample_user.id,
                'deployment_id': 'test-deployment'
            }
        )


class TestMatchRepository:
    """Tests for MatchRepository."""
    
    @pytest.fixture
    def match_repo(self, mock_dynamodb):
        """Create a MatchRepository instance with mocked DynamoDB."""
        return MatchRepository('test-deployment')
    
    @pytest.fixture
    def sample_match(self):
        """Create a sample match for testing."""
        return Match(
            id="test-match-id",
            deployment_id="test-deployment",
            participants=["user-1", "user-2"],
            scheduled_date=datetime.utcnow(),
            status="pending"
        )
    
    async def test_create_match(self, match_repo, sample_match, mock_dynamodb):
        """Test creating a match."""
        # Configure the mock
        mock_dynamodb['table'].put_item.return_value = {}
        
        # Call the method
        result = await match_repo.create(sample_match)
        
        # Verify the result
        assert result.id == sample_match.id
        assert result.participants == sample_match.participants
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].put_item.assert_called_once()
        call_args = mock_dynamodb['table'].put_item.call_args[1]
        assert 'Item' in call_args
        assert call_args['Item']['id'] == sample_match.id
        assert call_args['Item']['participants'] == sample_match.participants
    
    async def test_get_match(self, match_repo, sample_match, mock_dynamodb):
        """Test getting a match by ID."""
        # Convert datetime to string for the mock response
        match_dict = sample_match.dict()
        match_dict['scheduled_date'] = match_dict['scheduled_date'].isoformat()
        match_dict['created_at'] = match_dict['created_at'].isoformat()
        
        # Configure the mock
        mock_dynamodb['table'].get_item.return_value = {
            'Item': match_dict
        }
        
        # Call the method
        result = await match_repo.get(sample_match.id)
        
        # Verify the result
        assert result is not None
        assert result.id == sample_match.id
        assert result.participants == sample_match.participants
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].get_item.assert_called_once_with(
            Key={
                'id': sample_match.id,
                'deployment_id': 'test-deployment'
            }
        )
    
    async def test_get_all_matches(self, match_repo, sample_match, mock_dynamodb):
        """Test getting all matches."""
        # Convert datetime to string for the mock response
        match_dict = sample_match.dict()
        match_dict['scheduled_date'] = match_dict['scheduled_date'].isoformat()
        match_dict['created_at'] = match_dict['created_at'].isoformat()
        
        # Configure the mock
        mock_dynamodb['table'].query.return_value = {
            'Items': [match_dict]
        }
        
        # Call the method
        result = await match_repo.get_all()
        
        # Verify the result
        assert len(result) == 1
        assert result[0].id == sample_match.id
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].query.assert_called_once()
    
    async def test_get_matches_for_user(self, match_repo, sample_match, mock_dynamodb):
        """Test getting matches for a specific user."""
        # Convert datetime to string for the mock response
        match_dict = sample_match.dict()
        match_dict['scheduled_date'] = match_dict['scheduled_date'].isoformat()
        match_dict['created_at'] = match_dict['created_at'].isoformat()
        
        # Configure the mock
        mock_dynamodb['table'].query.return_value = {
            'Items': [match_dict]
        }
        
        # Call the method
        result = await match_repo.get_matches_for_user('user-1')
        
        # Verify the result
        assert len(result) == 1
        assert result[0].id == sample_match.id
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].query.assert_called_once()
        call_args = mock_dynamodb['table'].query.call_args[1]
        assert 'FilterExpression' in call_args
        assert call_args['FilterExpression'] == 'contains(participants, :participant_id)'
    
    async def test_update_match(self, match_repo, sample_match, mock_dynamodb):
        """Test updating a match."""
        # Convert datetime to string for the mock responses
        match_dict = sample_match.dict()
        match_dict['scheduled_date'] = match_dict['scheduled_date'].isoformat()
        match_dict['created_at'] = match_dict['created_at'].isoformat()
        
        updated_match_dict = {**match_dict, 'status': 'confirmed'}
        
        # Configure the mocks
        mock_dynamodb['table'].get_item.return_value = {
            'Item': match_dict
        }
        
        mock_dynamodb['table'].update_item.return_value = {
            'Attributes': updated_match_dict
        }
        
        # Call the method
        result = await match_repo.update(sample_match.id, {'status': 'confirmed'})
        
        # Verify the result
        assert result is not None
        assert result.status == 'confirmed'
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].update_item.assert_called_once()
    
    async def test_delete_match(self, match_repo, sample_match, mock_dynamodb):
        """Test deleting a match."""
        # Convert datetime to string for the mock response
        match_dict = sample_match.dict()
        match_dict['scheduled_date'] = match_dict['scheduled_date'].isoformat()
        match_dict['created_at'] = match_dict['created_at'].isoformat()
        
        # Configure the mocks
        mock_dynamodb['table'].get_item.return_value = {
            'Item': match_dict
        }
        
        mock_dynamodb['table'].delete_item.return_value = {}
        
        # Call the method
        result = await match_repo.delete(sample_match.id)
        
        # Verify the result
        assert result is True
        
        # Verify the mock was called correctly
        mock_dynamodb['table'].delete_item.assert_called_once_with(
            Key={
                'id': sample_match.id,
                'deployment_id': 'test-deployment'
            }
        )