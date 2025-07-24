"""
End-to-end integration tests for the complete user journey.
This test covers the full flow from user registration to matching and feedback.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.auth.jwt import create_access_token
from backend.api.main import app
from backend.api.models.match import Match, MatchStatus
from backend.api.models.user import Preferences, User


@pytest.fixture()
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture()
def mock_dynamodb():
    """Mock DynamoDB connections for testing."""
    with patch(
        "backend.api.repositories.dynamodb_connection.get_dynamodb_client"
    ) as mock_client:
        # Setup mock responses for DynamoDB operations
        mock_client.return_value = MagicMock()
        yield mock_client


@pytest.fixture()
def mock_ses():
    """Mock SES for email notifications."""
    with patch("backend.api.services.notification_service.send_email") as mock_ses:
        mock_ses.return_value = True
        yield mock_ses


@pytest.fixture()
def test_users():
    """Create test users for the journey."""
    return [
        {
            "id": f"test-user-{i}",
            "email": f"user{i}@example.com",
            "name": f"Test User {i}",
            "preferences": {
                "availability": ["Monday 9-10", "Wednesday 14-15"],
                "topics": ["Technology", "Coffee"],
                "meeting_length": 30,
            },
        }
        for i in range(1, 4)
    ]


@pytest.fixture()
def auth_headers(test_users):
    """Create authentication headers for test users."""
    headers = {}
    for user in test_users:
        token = create_access_token(
            data={
                "sub": user["id"],
                "email": user["email"],
                "deployment_id": "test-deployment",
            },
        )
        headers[user["id"]] = {"Authorization": f"Bearer {token}"}
    return headers


class TestUserJourney:
    """Test the complete user journey from registration to matching."""

    def test_full_user_journey(
        self, client, mock_dynamodb, mock_ses, test_users, auth_headers
    ):
        """
        Test the complete user journey:
        1. Register multiple users
        2. Update user preferences
        3. Run matching algorithm
        4. Check match results
        5. Update match status
        6. Submit feedback
        """
        # Step 1: Register users
        registered_users = []
        for user in test_users:
            # Mock user registration in DynamoDB
            with patch(
                "backend.api.repositories.user_repository.UserRepository.create_user",
                return_value=User(
                    **user,
                    deployment_id="test-deployment",
                    is_active=True,
                    is_paused=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ),
            ):
                response = client.post(
                    "/users/register",
                    json={
                        "email": user["email"],
                        "name": user["name"],
                        "preferences": user["preferences"],
                    },
                    headers=auth_headers[user["id"]],
                )

                assert response.status_code == 200
                assert response.json()["email"] == user["email"]
                registered_users.append(response.json())

        # Step 2: Update user preferences
        with patch(
            "backend.api.repositories.user_repository.UserRepository.update_user",
            return_value=User(
                **test_users[0],
                deployment_id="test-deployment",
                is_active=True,
                is_paused=False,
                preferences=Preferences(
                    availability=["Tuesday 11-12", "Thursday 15-16"],
                    topics=["Career", "Technology"],
                    meeting_length=45,
                ),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ):
            response = client.put(
                "/users/preferences",
                json={
                    "availability": ["Tuesday 11-12", "Thursday 15-16"],
                    "topics": ["Career", "Technology"],
                    "meeting_length": 45,
                },
                headers=auth_headers[test_users[0]["id"]],
            )

            assert response.status_code == 200
            assert response.json()["preferences"]["meeting_length"] == 45
            assert "Career" in response.json()["preferences"]["topics"]

        # Step 3: Run matching algorithm
        match_date = datetime.utcnow() + timedelta(days=1)
        match = Match(
            id="test-match-1",
            participants=[
                {
                    "id": test_users[0]["id"],
                    "name": test_users[0]["name"],
                    "email": test_users[0]["email"],
                },
                {
                    "id": test_users[1]["id"],
                    "name": test_users[1]["name"],
                    "email": test_users[1]["email"],
                },
            ],
            scheduled_date=match_date,
            status=MatchStatus.SCHEDULED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock the matching service
        with patch(
            "backend.api.services.matching_service.MatchingService.create_matches",
            return_value=[match],
        ):
            # Mock the match repository
            with patch(
                "backend.api.repositories.match_repository.MatchRepository.create_match",
                return_value=match,
            ):
                # Run matching via scheduler endpoint (normally triggered by cron)
                response = client.post(
                    "/scheduler/run-matching",
                    json={"deployment_id": "test-deployment"},
                )

                assert response.status_code == 200
                assert response.json()["matches_created"] == 1

        # Step 4: Check match results for user 1
        with patch(
            "backend.api.repositories.match_repository.MatchRepository.get_current_match",
            return_value=match,
        ):
            response = client.get(
                "/matches/current",
                headers=auth_headers[test_users[0]["id"]],
            )

            assert response.status_code == 200
            assert response.json()["id"] == "test-match-1"
            assert len(response.json()["participants"]) == 2

            # Also check for user 2
            response = client.get(
                "/matches/current",
                headers=auth_headers[test_users[1]["id"]],
            )

            assert response.status_code == 200
            assert response.json()["id"] == "test-match-1"

        # Step 5: Update match status
        updated_match = match.copy()
        updated_match.status = MatchStatus.COMPLETED

        with patch(
            "backend.api.repositories.match_repository.MatchRepository.get_match",
            return_value=match,
        ):
            with patch(
                "backend.api.repositories.match_repository.MatchRepository.update_match",
                return_value=updated_match,
            ):
                response = client.put(
                    "/matches/test-match-1/status",
                    json={"status": "completed"},
                    headers=auth_headers[test_users[0]["id"]],
                )

                assert response.status_code == 200
                assert response.json()["status"] == "completed"

        # Step 6: Submit feedback
        updated_match = match.copy()
        updated_match.status = MatchStatus.COMPLETED
        updated_match.feedback = [
            {
                "user_id": test_users[0]["id"],
                "rating": 5,
                "comments": "Great conversation!",
            },
        ]

        with patch(
            "backend.api.repositories.match_repository.MatchRepository.get_match",
            return_value=match,
        ):
            with patch(
                "backend.api.repositories.match_repository.MatchRepository.update_match",
                return_value=updated_match,
            ):
                response = client.post(
                    "/matches/feedback",
                    json={
                        "match_id": "test-match-1",
                        "rating": 5,
                        "comments": "Great conversation!",
                    },
                    headers=auth_headers[test_users[0]["id"]],
                )

                assert response.status_code == 200
                assert response.json()["feedback"][0]["rating"] == 5
                assert (
                    response.json()["feedback"][0]["comments"] == "Great conversation!"
                )

        # Step 7: Check match history
        with patch(
            "backend.api.repositories.match_repository.MatchRepository.get_user_matches",
            return_value=[updated_match],
        ):
            response = client.get(
                "/matches/history",
                headers=auth_headers[test_users[0]["id"]],
            )

            assert response.status_code == 200
            assert len(response.json()["matches"]) == 1
            assert response.json()["matches"][0]["id"] == "test-match-1"
            assert response.json()["matches"][0]["status"] == "completed"
            assert response.json()["matches"][0]["feedback"][0]["rating"] == 5
