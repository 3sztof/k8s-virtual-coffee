"""
Match management routes for the Virtual Coffee Platform.

This module provides API endpoints for match management, including:
- Current and historical match retrieval
- Match status and feedback management
- Match history filtering and pagination
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.api.auth.jwt import TokenData, get_current_token_data, get_current_user_id
from backend.api.models.match import Match
from backend.api.repositories.match_repository import MatchRepository
from backend.api.repositories.user_repository import UserRepository

# Create router
router = APIRouter(prefix="/matches", tags=["matches"])


class MatchFeedback(BaseModel):
    """Match feedback model."""

    rating: int  # 1-5 rating
    comment: Optional[str] = None
    attended: bool = True


class MatchWithParticipantDetails(BaseModel):
    """Match model with participant details."""

    id: str
    deployment_id: str
    participants: list[dict[str, Any]]  # User details instead of just IDs
    scheduled_date: datetime
    status: Optional[str] = None
    created_at: datetime
    notification_sent: bool = False
    feedback: Optional[dict[str, MatchFeedback]] = None


@router.get("/current", response_model=Optional[MatchWithParticipantDetails])
async def get_current_match(
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Get the current user's active match.

    Args:
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        Current match with participant details or None if no active match
    """
    # Create repositories
    match_repository = MatchRepository(token_data.deployment_id)
    user_repository = UserRepository(token_data.deployment_id)

    # Get all matches for the deployment
    all_matches = await match_repository.get_all()

    # Filter to matches containing the current user
    user_matches = [match for match in all_matches if user_id in match.participants]

    # Sort by scheduled date (newest first)
    user_matches.sort(key=lambda m: m.scheduled_date, reverse=True)

    # Get the most recent match
    current_match = user_matches[0] if user_matches else None

    if not current_match:
        return None

    # Get participant details
    participant_details = []
    for participant_id in current_match.participants:
        user = await user_repository.get(participant_id)
        if user:
            # Include only necessary user details
            participant_details.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                }
            )

    # Create response with participant details
    match_with_details = {
        "id": current_match.id,
        "deployment_id": current_match.deployment_id,
        "participants": participant_details,
        "scheduled_date": current_match.scheduled_date,
        "status": current_match.status,
        "created_at": current_match.created_at,
        "notification_sent": current_match.notification_sent,
        "feedback": current_match.feedback,
    }

    return match_with_details


@router.get("/history", response_model=list[MatchWithParticipantDetails])
async def get_match_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Get the current user's match history with pagination.

    Args:
        skip: Number of matches to skip (for pagination)
        limit: Maximum number of matches to return
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        List of matches with participant details
    """
    # Create repositories
    match_repository = MatchRepository(token_data.deployment_id)
    user_repository = UserRepository(token_data.deployment_id)

    # Get all matches for the deployment
    all_matches = await match_repository.get_all()

    # Filter to matches containing the current user
    user_matches = [match for match in all_matches if user_id in match.participants]

    # Sort by scheduled date (newest first)
    user_matches.sort(key=lambda m: m.scheduled_date, reverse=True)

    # Apply pagination
    paginated_matches = user_matches[skip : skip + limit]

    # Get participant details for each match
    matches_with_details = []
    for match in paginated_matches:
        participant_details = []
        for participant_id in match.participants:
            user = await user_repository.get(participant_id)
            if user:
                # Include only necessary user details
                participant_details.append(
                    {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                    }
                )

        # Create response with participant details
        match_with_details = {
            "id": match.id,
            "deployment_id": match.deployment_id,
            "participants": participant_details,
            "scheduled_date": match.scheduled_date,
            "status": match.status,
            "created_at": match.created_at,
            "notification_sent": match.notification_sent,
            "feedback": match.feedback,
        }

        matches_with_details.append(match_with_details)

    return matches_with_details


@router.get("/{match_id}", response_model=MatchWithParticipantDetails)
async def get_match_by_id(
    match_id: str,
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Get a specific match by ID.

    Args:
        match_id: Match ID
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        Match with participant details

    Raises:
        HTTPException: If match not found or user not authorized
    """
    # Create repositories
    match_repository = MatchRepository(token_data.deployment_id)
    user_repository = UserRepository(token_data.deployment_id)

    # Get match from database
    match = await match_repository.get(match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Check if user is a participant
    if user_id not in match.participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this match",
        )

    # Get participant details
    participant_details = []
    for participant_id in match.participants:
        user = await user_repository.get(participant_id)
        if user:
            # Include only necessary user details
            participant_details.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                }
            )

    # Create response with participant details
    match_with_details = {
        "id": match.id,
        "deployment_id": match.deployment_id,
        "participants": participant_details,
        "scheduled_date": match.scheduled_date,
        "status": match.status,
        "created_at": match.created_at,
        "notification_sent": match.notification_sent,
        "feedback": match.feedback,
    }

    return match_with_details


@router.post("/{match_id}/feedback", response_model=Match)
async def submit_match_feedback(
    match_id: str,
    feedback: MatchFeedback,
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Submit feedback for a match.

    Args:
        match_id: Match ID
        feedback: Feedback data
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        Updated match

    Raises:
        HTTPException: If match not found or user not authorized
    """
    # Create match repository
    match_repository = MatchRepository(token_data.deployment_id)

    # Get match from database
    match = await match_repository.get(match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Check if user is a participant
    if user_id not in match.participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit feedback for this match",
        )

    # Initialize feedback dictionary if not exists
    if not match.feedback:
        match.feedback = {}

    # Add feedback
    match.feedback[user_id] = {
        "rating": feedback.rating,
        "comment": feedback.comment,
        "attended": feedback.attended,
    }

    # Update match status if all participants have submitted feedback
    if len(match.feedback) == len(match.participants):
        match.status = "completed"

    # Save updated match to database
    updated_match = await match_repository.update(match)
    return updated_match


@router.put("/{match_id}/status", response_model=Match)
async def update_match_status(
    match_id: str,
    status: str,
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Update the status of a match.

    Args:
        match_id: Match ID
        status: New status
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        Updated match

    Raises:
        HTTPException: If match not found or user not authorized
    """
    # Create match repository
    match_repository = MatchRepository(token_data.deployment_id)

    # Get match from database
    match = await match_repository.get(match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Check if user is a participant
    if user_id not in match.participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this match",
        )

    # Validate status
    valid_statuses = ["pending", "scheduled", "completed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    # Update match status
    match.status = status

    # Save updated match to database
    updated_match = await match_repository.update(match)
    return updated_match
