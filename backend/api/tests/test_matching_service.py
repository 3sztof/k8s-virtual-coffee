"""
Tests for the matching service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import random

from backend.api.models.user import User, Preferences
from backend.api.models.match import Match
from backend.api.models.config import DeploymentConfig
from backend.api.services.matching_service import MatchingService


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_match_repository():
    """Create a mock match repository."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_config_service():
    """Create a mock config service."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def matching_service(mock_user_repository, mock_match_repository, mock_config_service):
    """Create a matching service with mocked dependencies."""
    service = MatchingService("test-deployment")
    service.user_repository = mock_user_repository
    service.match_repository = mock_match_repository
    service.config_service = mock_config_service
    return service


def create_test_user(user_id, name, topics=None, availability=None, meeting_length=30):
    """Helper function to create test users."""
    return User(
        id=f"user-{user_id}",
        email=f"user{user_id}@example.com",
        name=name,
        deployment_id="test-deployment",
        preferences=Preferences(
            topics=topics or [],
            availability=availability or [],
            meeting_length=meeting_length
        )
    )


def create_test_match(match_id, participants, created_days_ago=0):
    """Helper function to create test matches."""
    created_at = datetime.utcnow() - timedelta(days=created_days_ago)
    return Match(
        id=f"match-{match_id}",
        deployment_id="test-deployment",
        participants=participants,
        scheduled_date=created_at + timedelta(days=1),
        created_at=created_at
    )


class TestMatchingService:
    """Tests for the MatchingService class."""

    async def test_get_eligible_users(self, matching_service, mock_user_repository):
        """Test getting eligible users."""
        # Setup
        expected_users = [
            create_test_user(1, "User 1"),
            create_test_user(2, "User 2")
        ]
        mock_user_repository.get_all.return_value = expected_users

        # Execute
        result = await matching_service.get_eligible_users()

        # Verify
        mock_user_repository.get_all.assert_called_once_with({
            'is_active': True,
            'is_paused': False
        })
        assert result == expected_users

    async def test_get_recent_matches(self, matching_service, mock_match_repository):
        """Test getting recent matches."""
        # Setup
        all_matches = [
            create_test_match(1, ["user-1", "user-2"], created_days_ago=5),
            create_test_match(2, ["user-1", "user-3"], created_days_ago=15),
            create_test_match(3, ["user-2", "user-3"], created_days_ago=40)
        ]
        mock_match_repository.get_all.return_value = all_matches

        # Execute
        result = await matching_service.get_recent_matches(lookback_days=30)

        # Verify
        assert len(result) == 2
        assert result[0].id == "match-1"
        assert result[1].id == "match-2"

    async def test_build_history_graph(self, matching_service):
        """Test building the weighted history graph."""
        # Setup
        # Create matches with different creation dates to test weighting
        now = datetime.utcnow()
        recent_match = create_test_match(1, ["user-1", "user-2"])
        recent_match.created_at = now - timedelta(days=5)
        
        older_match = create_test_match(2, ["user-1", "user-3"])
        older_match.created_at = now - timedelta(days=15)
        
        oldest_match = create_test_match(3, ["user-2", "user-3", "user-4"])
        oldest_match.created_at = now - timedelta(days=25)
        
        matching_service.get_recent_matches = AsyncMock()
        matching_service.get_recent_matches.return_value = [
            recent_match, older_match, oldest_match
        ]

        # Execute
        result = await matching_service.build_history_graph(lookback_days=30)

        # Verify
        # Check that all users are in the graph
        assert "user-1" in result
        assert "user-2" in result
        assert "user-3" in result
        assert "user-4" in result
        
        # Check that all connections are present
        assert "user-2" in result["user-1"]
        assert "user-3" in result["user-1"]
        assert "user-1" in result["user-2"]
        assert "user-3" in result["user-2"]
        assert "user-4" in result["user-2"]
        assert "user-1" in result["user-3"]
        assert "user-2" in result["user-3"]
        assert "user-4" in result["user-3"]
        assert "user-2" in result["user-4"]
        assert "user-3" in result["user-4"]
        
        # Check that weights are higher for more recent matches
        assert result["user-1"]["user-2"] > result["user-1"]["user-3"]
        assert result["user-2"]["user-3"] > result["user-2"]["user-4"]
        
        # Check that weights are between 0 and 1
        for user_id, connections in result.items():
            for other_id, weight in connections.items():
                assert 0 <= weight <= 1, f"Weight {weight} for {user_id}->{other_id} is out of range"

    def test_calculate_match_score(self, matching_service):
        """Test calculating match scores between users."""
        # Setup
        user1 = create_test_user(
            1, "User 1", 
            topics=["Technology", "Coffee", "Books"],
            availability=["Monday 9-10", "Wednesday 14-15"],
            meeting_length=30
        )
        
        user2 = create_test_user(
            2, "User 2", 
            topics=["Technology", "Sports", "Movies"],
            availability=["Monday 9-10", "Tuesday 11-12"],
            meeting_length=45
        )
        
        user3 = create_test_user(
            3, "User 3", 
            topics=["Coffee", "Books", "Music"],
            availability=["Wednesday 14-15", "Friday 10-11"],
            meeting_length=30
        )
        
        # Execute
        score1_2 = matching_service.calculate_match_score(user1, user2)
        score1_3 = matching_service.calculate_match_score(user1, user3)
        score2_3 = matching_service.calculate_match_score(user2, user3)
        
        # Verify
        # User 1 and 2 share 1/5 topics, 1/3 availability slots, and have 15 min difference in meeting length
        # User 1 and 3 share 2/4 topics, 1/3 availability slots, and have 0 min difference in meeting length
        # User 2 and 3 share 0/5 topics, 0/4 availability slots, and have 15 min difference in meeting length
        
        assert score1_3 > score1_2 > score2_3
        assert 0 <= score1_2 <= 1
        assert 0 <= score1_3 <= 1
        assert 0 <= score2_3 <= 1

    async def test_create_matches_with_meeting_size_2(self, matching_service, mock_user_repository, mock_match_repository, mock_config_service):
        """Test creating matches with meeting size 2."""
        # Setup
        users = [
            create_test_user(1, "User 1"),
            create_test_user(2, "User 2"),
            create_test_user(3, "User 3"),
            create_test_user(4, "User 4")
        ]
        
        config = DeploymentConfig(
            deployment_id="test-deployment",
            schedule="0 9 * * 1",
            meeting_size=2
        )
        
        mock_user_repository.get_all.return_value = users
        mock_config_service.get_config.return_value = config
        
        # Mock history graph to be empty (no recent matches)
        matching_service.build_history_graph = AsyncMock(return_value={})
        
        # Mock match creation
        async def mock_create_match(match):
            return match
        
        mock_match_repository.create.side_effect = mock_create_match
        
        # Set a fixed seed for reproducibility
        random.seed(42)
        
        # Execute
        result = await matching_service.create_matches()
        
        # Verify
        assert len(result) == 2  # Should create 2 matches with 4 users and meeting size 2
        
        # Check that each user is in exactly one match
        matched_users = set()
        for match in result:
            assert len(match.participants) == 2
            for user_id in match.participants:
                assert user_id not in matched_users
                matched_users.add(user_id)
        
        assert len(matched_users) == 4

    async def test_create_matches_with_meeting_size_3(self, matching_service, mock_user_repository, mock_match_repository, mock_config_service):
        """Test creating matches with meeting size 3."""
        # Setup
        users = [
            create_test_user(1, "User 1"),
            create_test_user(2, "User 2"),
            create_test_user(3, "User 3"),
            create_test_user(4, "User 4"),
            create_test_user(5, "User 5"),
            create_test_user(6, "User 6")
        ]
        
        config = DeploymentConfig(
            deployment_id="test-deployment",
            schedule="0 9 * * 1",
            meeting_size=3
        )
        
        mock_user_repository.get_all.return_value = users
        mock_config_service.get_config.return_value = config
        
        # Mock history graph to be empty (no recent matches)
        matching_service.build_history_graph = AsyncMock(return_value={})
        
        # Mock match creation
        async def mock_create_match(match):
            return match
        
        mock_match_repository.create.side_effect = mock_create_match
        
        # Set a fixed seed for reproducibility
        random.seed(42)
        
        # Execute
        result = await matching_service.create_matches()
        
        # Verify
        assert len(result) == 2  # Should create 2 matches with 6 users and meeting size 3
        
        # Check that each user is in exactly one match
        matched_users = set()
        for match in result:
            assert len(match.participants) == 3
            for user_id in match.participants:
                assert user_id not in matched_users
                matched_users.add(user_id)
        
        assert len(matched_users) == 6

    async def test_create_matches_with_history_avoidance(self, matching_service, mock_user_repository, mock_match_repository, mock_config_service):
        """Test that the matching algorithm avoids recent matches."""
        # Setup
        users = [
            create_test_user(1, "User 1"),
            create_test_user(2, "User 2"),
            create_test_user(3, "User 3"),
            create_test_user(4, "User 4")
        ]
        
        config = DeploymentConfig(
            deployment_id="test-deployment",
            schedule="0 9 * * 1",
            meeting_size=2
        )
        
        mock_user_repository.get_all.return_value = users
        mock_config_service.get_config.return_value = config
        
        # Mock weighted history graph with recent matches
        history_graph = {
            "user-1": {"user-2": 0.8},  # High weight = very recent match
            "user-2": {"user-1": 0.8},
            "user-3": {"user-4": 0.8},
            "user-4": {"user-3": 0.8}
        }
        
        matching_service.build_history_graph = AsyncMock(return_value=history_graph)
        
        # Mock match creation
        async def mock_create_match(match):
            return match
        
        mock_match_repository.create.side_effect = mock_create_match
        
        # Set a fixed seed for reproducibility
        random.seed(42)
        
        # Execute
        result = await matching_service.create_matches()
        
        # Verify
        assert len(result) == 2  # Should create 2 matches with 4 users and meeting size 2
        
        # Check that the matches avoid recent pairings
        for match in result:
            participants = match.participants
            assert not (
                ("user-1" in participants and "user-2" in participants) or
                ("user-3" in participants and "user-4" in participants)
            )

    async def test_create_matches_with_odd_number_of_users(self, matching_service, mock_user_repository, mock_match_repository, mock_config_service):
        """Test creating matches with an odd number of users."""
        # Setup
        users = [
            create_test_user(1, "User 1"),
            create_test_user(2, "User 2"),
            create_test_user(3, "User 3"),
            create_test_user(4, "User 4"),
            create_test_user(5, "User 5")
        ]
        
        config = DeploymentConfig(
            deployment_id="test-deployment",
            schedule="0 9 * * 1",
            meeting_size=2
        )
        
        mock_user_repository.get_all.return_value = users
        mock_config_service.get_config.return_value = config
        
        # Mock history graph to be empty (no recent matches)
        matching_service.build_history_graph = AsyncMock(return_value={})
        
        # Mock match creation
        async def mock_create_match(match):
            return match
        
        mock_match_repository.create.side_effect = mock_create_match
        
        # Set a fixed seed for reproducibility
        random.seed(42)
        
        # Execute
        result = await matching_service.create_matches()
        
        # Verify
        assert len(result) == 2  # Should create 2 matches with 5 users and meeting size 2
                                 # One match will have 2 users, one will have 3 users
        
        # Check that each user is in exactly one match
        matched_users = set()
        for match in result:
            assert 2 <= len(match.participants) <= 3
            for user_id in match.participants:
                assert user_id not in matched_users
                matched_users.add(user_id)
        
        assert len(matched_users) == 5

    async def test_create_matches_with_not_enough_users(self, matching_service, mock_user_repository, mock_config_service):
        """Test creating matches when there aren't enough eligible users."""
        # Setup
        users = [
            create_test_user(1, "User 1")
        ]
        
        config = DeploymentConfig(
            deployment_id="test-deployment",
            schedule="0 9 * * 1",
            meeting_size=2
        )
        
        mock_user_repository.get_all.return_value = users
        mock_config_service.get_config.return_value = config
        
        # Execute
        result = await matching_service.create_matches()
        
        # Verify
        assert len(result) == 0  # Should not create any matches with only 1 user

    async def test_create_matches_with_no_config(self, matching_service, mock_user_repository, mock_config_service):
        """Test creating matches when there's no configuration."""
        # Setup
        users = [
            create_test_user(1, "User 1"),
            create_test_user(2, "User 2")
        ]
        
        mock_user_repository.get_all.return_value = users
        mock_config_service.get_config.return_value = None
        
        # Execute
        result = await matching_service.create_matches()
        
        # Verify
        assert len(result) == 0  # Should not create any matches without a config
        
    async def test_create_matches_with_preferences(self, matching_service, mock_user_repository, mock_match_repository, mock_config_service):
        """Test that the matching algorithm considers user preferences."""
        # Setup
        # Create users with specific preferences to test preference-based matching
        user1 = create_test_user(
            1, "User 1", 
            topics=["Technology", "Coffee", "Books"],
            availability=["Monday 9-10", "Wednesday 14-15"],
            meeting_length=30
        )
        
        user2 = create_test_user(
            2, "User 2", 
            topics=["Technology", "Sports", "Movies"],
            availability=["Monday 9-10", "Tuesday 11-12"],
            meeting_length=45
        )
        
        user3 = create_test_user(
            3, "User 3", 
            topics=["Coffee", "Books", "Music"],
            availability=["Wednesday 14-15", "Friday 10-11"],
            meeting_length=30
        )
        
        user4 = create_test_user(
            4, "User 4", 
            topics=["Sports", "Movies", "Gaming"],
            availability=["Tuesday 11-12", "Thursday 13-14"],
            meeting_length=45
        )
        
        users = [user1, user2, user3, user4]
        
        config = DeploymentConfig(
            deployment_id="test-deployment",
            schedule="0 9 * * 1",
            meeting_size=2
        )
        
        mock_user_repository.get_all.return_value = users
        mock_config_service.get_config.return_value = config
        
        # Mock history graph to be empty (no recent matches)
        matching_service.build_history_graph = AsyncMock(return_value={})
        
        # Mock match creation
        async def mock_create_match(match):
            return match
        
        mock_match_repository.create.side_effect = mock_create_match
        
        # Set a fixed seed for reproducibility
        random.seed(42)
        
        # Execute
        result = await matching_service.create_matches()
        
        # Verify
        assert len(result) == 2  # Should create 2 matches with 4 users and meeting size 2
        
        # Check that each user is in exactly one match
        matched_users = set()
        for match in result:
            assert len(match.participants) == 2
            for user_id in match.participants:
                assert user_id not in matched_users
                matched_users.add(user_id)
        
        assert len(matched_users) == 4
        
        # Check that users with similar preferences are matched together
        # Based on our preferences:
        # - User 1 and User 3 share topics (Coffee, Books) and availability (Wednesday 14-15)
        # - User 2 and User 4 share topics (Sports, Movies) and availability (Tuesday 11-12)
        
        # Find the matches
        match1 = next((m for m in result if "user-1" in m.participants), None)
        match2 = next((m for m in result if "user-2" in m.participants), None)
        
        # Verify that users with similar preferences are matched
        assert match1 is not None
        assert match2 is not None
        
        # Check if User 1 is matched with User 3 and User 2 is matched with User 4
        # This is the optimal matching based on preferences
        if "user-1" in match1.participants:
            assert "user-3" in match1.participants
        if "user-2" in match2.participants:
            assert "user-4" in match2.participants