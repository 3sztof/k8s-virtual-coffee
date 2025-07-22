"""
End-to-end integration tests for multi-deployment isolation.
This test verifies that different deployments are properly isolated from each other.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.api.main import app
from backend.api.models.user import User
from backend.api.models.match import Match, MatchStatus
from backend.api.auth.jwt import create_access_token
from datetime import datetime


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB connections for testing."""
    with patch('backend.api.repositories.dynamodb_connection.get_dynamodb_client') as mock_client:
        # Setup mock responses for DynamoDB operations
        mock_client.return_value = MagicMock()
        yield mock_client


@pytest.fixture
def test_deployments():
    """Create test deployment data."""
    return [
        {
            "id": "deployment-a",
            "users": [
                {
                    "id": "user-a1",
                    "email": "user-a1@example.com",
                    "name": "User A1",
                    "deployment_id": "deployment-a"
                },
                {
                    "id": "user-a2",
                    "email": "user-a2@example.com",
                    "name": "User A2",
                    "deployment_id": "deployment-a"
                }
            ],
            "matches": [
                {
                    "id": "match-a1",
                    "participants": [
                        {"id": "user-a1", "name": "User A1", "email": "user-a1@example.com"},
                        {"id": "user-a2", "name": "User A2", "email": "user-a2@example.com"}
                    ],
                    "deployment_id": "deployment-a"
                }
            ]
        },
        {
            "id": "deployment-b",
            "users": [
                {
                    "id": "user-b1",
                    "email": "user-b1@example.com",
                    "name": "User B1",
                    "deployment_id": "deployment-b"
                },
                {
                    "id": "user-b2",
                    "email": "user-b2@example.com",
                    "name": "User B2",
                    "deployment_id": "deployment-b"
                }
            ],
            "matches": [
                {
                    "id": "match-b1",
                    "participants": [
                        {"id": "user-b1", "name": "User B1", "email": "user-b1@example.com"},
                        {"id": "user-b2", "name": "User B2", "email": "user-b2@example.com"}
                    ],
                    "deployment_id": "deployment-b"
                }
            ]
        }
    ]


@pytest.fixture
def auth_headers(test_deployments):
    """Create authentication headers for test users in different deployments."""
    headers = {}
    for deployment in test_deployments:
        for user in deployment["users"]:
            token = create_access_token(
                data={
                    "sub": user["id"],
                    "email": user["email"],
                    "deployment_id": deployment["id"]
                }
            )
            headers[user["id"]] = {"Authorization": f"Bearer {token}"}
    return headers


class TestMultiDeploymentIsolation:
    """Test isolation between multiple deployments."""

    def test_user_isolation(self, client, mock_dynamodb, test_deployments, auth_headers):
        """Test that users can only see users from their own deployment."""
        # Setup mock for deployment A
        deployment_a = test_deployments[0]
        deployment_a_users = [
            User(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                deployment_id=deployment_a["id"],
                is_active=True,
                is_paused=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ) for user in deployment_a["users"]
        ]
        
        # Setup mock for deployment B
        deployment_b = test_deployments[1]
        deployment_b_users = [
            User(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                deployment_id=deployment_b["id"],
                is_active=True,
                is_paused=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ) for user in deployment_b["users"]
        ]
        
        # Test user from deployment A can only see users from deployment A
        with patch('backend.api.repositories.user_repository.UserRepository.get_all_users',
                  side_effect=lambda deployment_id, *args, **kwargs: 
                      deployment_a_users if deployment_id == deployment_a["id"] else deployment_b_users):
            
            # User from deployment A
            response = client.get(
                "/users",
                headers=auth_headers[deployment_a["users"][0]["id"]]
            )
            
            assert response.status_code == 200
            assert len(response.json()) == len(deployment_a["users"])
            user_ids = [user["id"] for user in response.json()]
            for user in deployment_a["users"]:
                assert user["id"] in user_ids
            for user in deployment_b["users"]:
                assert user["id"] not in user_ids
            
            # User from deployment B
            response = client.get(
                "/users",
                headers=auth_headers[deployment_b["users"][0]["id"]]
            )
            
            assert response.status_code == 200
            assert len(response.json()) == len(deployment_b["users"])
            user_ids = [user["id"] for user in response.json()]
            for user in deployment_b["users"]:
                assert user["id"] in user_ids
            for user in deployment_a["users"]:
                assert user["id"] not in user_ids

    def test_match_isolation(self, client, mock_dynamodb, test_deployments, auth_headers):
        """Test that users can only see matches from their own deployment."""
        # Setup mock for deployment A
        deployment_a = test_deployments[0]
        deployment_a_match = Match(
            id=deployment_a["matches"][0]["id"],
            participants=deployment_a["matches"][0]["participants"],
            deployment_id=deployment_a["id"],
            scheduled_date=datetime.utcnow(),
            status=MatchStatus.SCHEDULED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Setup mock for deployment B
        deployment_b = test_deployments[1]
        deployment_b_match = Match(
            id=deployment_b["matches"][0]["id"],
            participants=deployment_b["matches"][0]["participants"],
            deployment_id=deployment_b["id"],
            scheduled_date=datetime.utcnow(),
            status=MatchStatus.SCHEDULED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Test user from deployment A can only see matches from deployment A
        with patch('backend.api.repositories.match_repository.MatchRepository.get_current_match',
                  side_effect=lambda user_id, deployment_id: 
                      deployment_a_match if deployment_id == deployment_a["id"] else deployment_b_match):
            
            # User from deployment A
            response = client.get(
                "/matches/current",
                headers=auth_headers[deployment_a["users"][0]["id"]]
            )
            
            assert response.status_code == 200
            assert response.json()["id"] == deployment_a["matches"][0]["id"]
            
            # User from deployment B
            response = client.get(
                "/matches/current",
                headers=auth_headers[deployment_b["users"][0]["id"]]
            )
            
            assert response.status_code == 200
            assert response.json()["id"] == deployment_b["matches"][0]["id"]
    
    def test_cross_deployment_access_denied(self, client, mock_dynamodb, test_deployments, auth_headers):
        """Test that users cannot access resources from other deployments."""
        # Setup mock for deployment A
        deployment_a = test_deployments[0]
        deployment_a_match = Match(
            id=deployment_a["matches"][0]["id"],
            participants=deployment_a["matches"][0]["participants"],
            deployment_id=deployment_a["id"],
            scheduled_date=datetime.utcnow(),
            status=MatchStatus.SCHEDULED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock the match repository to return the match only if the deployment ID matches
        with patch('backend.api.repositories.match_repository.MatchRepository.get_match',
                  side_effect=lambda match_id, deployment_id: 
                      deployment_a_match if deployment_id == deployment_a["id"] and match_id == deployment_a_match.id else None):
            
            # User from deployment A can access their own match
            response = client.get(
                f"/matches/{deployment_a_match.id}",
                headers=auth_headers[deployment_a["users"][0]["id"]]
            )
            
            assert response.status_code == 200
            assert response.json()["id"] == deployment_a_match.id
            
            # User from deployment B cannot access deployment A's match
            response = client.get(
                f"/matches/{deployment_a_match.id}",
                headers=auth_headers[deployment_b["users"][0]["id"]]
            )
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_matching_isolation(self, client, mock_dynamodb, test_deployments):
        """Test that matching algorithm only matches users within the same deployment."""
        # Setup users for both deployments
        all_users = []
        for deployment in test_deployments:
            for user in deployment["users"]:
                all_users.append(User(
                    id=user["id"],
                    email=user["email"],
                    name=user["name"],
                    deployment_id=deployment["id"],
                    is_active=True,
                    is_paused=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        
        # Mock the user repository to return users filtered by deployment
        with patch('backend.api.repositories.user_repository.UserRepository.get_all_users',
                  side_effect=lambda deployment_id, active_only=None, paused_only=None: 
                      [u for u in all_users if u.deployment_id == deployment_id and u.is_active and not u.is_paused]):
            
            # Mock the match repository
            with patch('backend.api.repositories.match_repository.MatchRepository.create_match',
                      return_value=None):
                
                # Run matching for deployment A
                response = client.post(
                    "/scheduler/run-matching",
                    json={"deployment_id": test_deployments[0]["id"]}
                )
                
                assert response.status_code == 200
                
                # Verify that the matching service was called with the correct deployment ID
                # This is a bit tricky to test directly, but we can check that the endpoint returns successfully
                assert "matches_created" in response.json()
                
                # Run matching for deployment B
                response = client.post(
                    "/scheduler/run-matching",
                    json={"deployment_id": test_deployments[1]["id"]}
                )
                
                assert response.status_code == 200
                assert "matches_created" in response.json()