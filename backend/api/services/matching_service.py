"""
Matching service implementation for the Virtual Coffee Platform.

This service handles the matching algorithm for virtual coffee meetings,
including random matching with historical avoidance, preference consideration,
and configurable meeting sizes.
"""
import logging
import random
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from backend.api.models.user import User
from backend.api.models.match import Match, MatchCreate
from backend.api.models.config import DeploymentConfig
from backend.api.repositories.user_repository import UserRepository
from backend.api.repositories.match_repository import MatchRepository
from backend.api.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Matching service implementation for the Virtual Coffee Platform.
    
    This service is responsible for:
    1. Creating random matches between users
    2. Avoiding recent matches between the same users
    3. Considering user preferences when possible
    4. Supporting configurable meeting sizes
    """
    
    def __init__(self, deployment_id: str):
        """
        Initialize the matching service.
        
        Args:
            deployment_id: The deployment ID for multi-tenancy
        """
        self.deployment_id = deployment_id
        self.user_repository = UserRepository(deployment_id)
        self.match_repository = MatchRepository(deployment_id)
        self.config_service = ConfigService()
    
    async def get_eligible_users(self) -> List[User]:
        """
        Get all eligible users for matching.
        
        Returns:
            A list of users eligible for matching (active and not paused)
        """
        return await self.user_repository.get_all({
            'is_active': True,
            'is_paused': False
        })
    
    async def get_recent_matches(self, lookback_days: int = 30) -> List[Match]:
        """
        Get recent matches within the specified lookback period.
        
        Args:
            lookback_days: Number of days to look back for historical matches
            
        Returns:
            A list of recent matches
        """
        # Get all matches
        all_matches = await self.match_repository.get_all()
        
        # Filter to recent matches
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        recent_matches = [
            match for match in all_matches
            if match.created_at >= cutoff_date
        ]
        
        return recent_matches
    
    async def build_history_graph(self, lookback_days: int = 30) -> Dict[str, Dict[str, float]]:
        """
        Build a weighted history graph of recent matches between users.
        
        Args:
            lookback_days: Number of days to look back for historical matches
            
        Returns:
            A dictionary mapping user IDs to dictionaries of recently matched user IDs with weights
            Higher weights indicate more recent or frequent matches
        """
        recent_matches = await self.get_recent_matches(lookback_days)
        
        # Sort matches by date (newest first)
        sorted_matches = sorted(
            recent_matches, 
            key=lambda m: m.created_at, 
            reverse=True
        )
        
        # Build weighted graph of recent matches
        history_graph: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Calculate the maximum age in days for normalization
        now = datetime.utcnow()
        max_age = lookback_days
        
        for match in sorted_matches:
            # Calculate match age in days
            match_age = (now - match.created_at).days
            
            # Calculate recency weight (1.0 for newest, decreasing for older)
            # More recent matches get higher weights
            recency_weight = 1.0 - (match_age / max_age)
            
            # For each pair of participants in the match
            participants = match.participants
            for i, user_id in enumerate(participants):
                # Add all other participants as connections with weights
                for j, other_id in enumerate(participants):
                    if i != j:  # Don't add self-connections
                        # Add recency weight to existing weight (if any)
                        history_graph[user_id][other_id] += recency_weight
        
        return dict(history_graph)
    
    def calculate_match_score(self, user1: User, user2: User) -> float:
        """
        Calculate a compatibility score between two users based on preferences.
        
        This method evaluates multiple factors to determine how compatible two users are:
        1. Topic similarity - How many interests they share
        2. Meeting length compatibility - How close their preferred meeting durations are
        3. Availability compatibility - How many time slots they have in common
        
        Args:
            user1: First user
            user2: Second user
            
        Returns:
            A score between 0 and 1, where higher is better
        """
        # Define weights for different factors
        TOPIC_WEIGHT = 0.4
        LENGTH_WEIGHT = 0.2
        AVAIL_WEIGHT = 0.4
        
        # Track scores and weights
        weighted_score = 0.0
        total_weight = 0.0
        
        # Factor 1: Common topics (weighted at 40%)
        user1_topics = set(user1.preferences.topics)
        user2_topics = set(user2.preferences.topics)
        
        if user1_topics and user2_topics:  # Only if both have topics
            common_topics = user1_topics.intersection(user2_topics)
            all_topics = user1_topics.union(user2_topics)
            
            if all_topics:  # Avoid division by zero
                # Jaccard similarity: size of intersection / size of union
                topic_score = len(common_topics) / len(all_topics)
                weighted_score += topic_score * TOPIC_WEIGHT
                total_weight += TOPIC_WEIGHT
        
        # Factor 2: Meeting length preference compatibility (weighted at 20%)
        if user1.preferences.meeting_length and user2.preferences.meeting_length:
            # Calculate similarity based on how close the preferred lengths are
            length_diff = abs(user1.preferences.meeting_length - user2.preferences.meeting_length)
            max_diff = 45  # Maximum expected difference (e.g., 15 vs 60 minutes)
            length_score = 1 - min(length_diff / max_diff, 1.0)  # Cap at 1.0
            weighted_score += length_score * LENGTH_WEIGHT
            total_weight += LENGTH_WEIGHT
        
        # Factor 3: Availability compatibility (weighted at 40%)
        user1_avail = set(user1.preferences.availability)
        user2_avail = set(user2.preferences.availability)
        
        if user1_avail and user2_avail:  # Only if both have availability preferences
            common_avail = user1_avail.intersection(user2_avail)
            if common_avail:
                # Calculate overlap coefficient: size of intersection / size of smaller set
                # This rewards having at least one common slot, even if users have many slots
                avail_score = len(common_avail) / min(len(user1_avail), len(user2_avail))
                weighted_score += avail_score * AVAIL_WEIGHT
                total_weight += AVAIL_WEIGHT
        
        # Return normalized score or 0.5 if no factors were considered
        if total_weight > 0:
            return weighted_score / total_weight
        else:
            # Default score when no preferences are available
            return 0.5
    
    async def create_matches(self, scheduled_date: Optional[datetime] = None) -> List[Match]:
        """
        Create matches between eligible users.
        
        This method orchestrates the matching process by:
        1. Getting the deployment configuration to determine meeting size
        2. Retrieving all eligible users (active and not paused)
        3. Building a history graph to avoid recent matches
        4. Creating optimal matches based on preferences and history
        
        Args:
            scheduled_date: The scheduled date for the matches (defaults to now)
            
        Returns:
            A list of created matches
        """
        # Get deployment configuration
        config = await self.config_service.get_config(self.deployment_id)
        if not config:
            logger.error(f"No configuration found for deployment {self.deployment_id}")
            return []
        
        # Get eligible users
        eligible_users = await self.get_eligible_users()
        if len(eligible_users) < 2:
            logger.warning(f"Not enough eligible users for matching in deployment {self.deployment_id}")
            return []
        
        # Log the matching process
        logger.info(f"Starting matching process for {len(eligible_users)} users in deployment {self.deployment_id}")
        
        # Build weighted history graph for historical avoidance
        history_graph = await self.build_history_graph()
        
        # Set meeting size from configuration
        meeting_size = config.meeting_size
        logger.info(f"Using meeting size of {meeting_size} from configuration")
        
        # Set scheduled date if not provided
        if scheduled_date is None:
            scheduled_date = datetime.utcnow()
        
        # Create matches using the optimal matching algorithm
        matches = await self._create_optimal_matches(eligible_users, history_graph, meeting_size, scheduled_date)
        
        # Log the results
        logger.info(f"Created {len(matches)} matches for {len(eligible_users)} users")
        for i, match in enumerate(matches):
            logger.debug(f"Match {i+1}: {len(match.participants)} participants")
        
        return matches
    
    async def _create_optimal_matches(
        self, 
        users: List[User], 
        history_graph: Dict[str, Dict[str, float]], 
        meeting_size: int, 
        scheduled_date: datetime
    ) -> List[Match]:
        """
        Create optimal matches between users based on history and preferences.
        
        This algorithm creates matches by:
        1. Calculating compatibility scores between all user pairs
        2. Penalizing pairs that have met recently (based on weighted history)
        3. Creating groups of users based on the configured meeting size
        4. Handling leftover users to ensure everyone is matched
        
        Args:
            users: List of eligible users
            history_graph: Weighted graph of recent matches
            meeting_size: Number of users per match (from configuration)
            scheduled_date: The scheduled date for the matches
            
        Returns:
            A list of created matches
        """
        # Constants for algorithm tuning
        HISTORY_PENALTY_FACTOR = 0.7  # How much to penalize recent matches (lower = stronger penalty)
        MIN_GROUP_SIZE = 2  # Minimum users required for a valid match
        
        # Create user lookup dictionary for quick access
        user_dict = {user.id: user for user in users}
        
        # Shuffle users to ensure randomness when scores are equal
        shuffled_users = users.copy()
        random.shuffle(shuffled_users)
        
        # Calculate all possible pairs and their scores
        pair_scores: Dict[Tuple[str, str], float] = {}
        for i, user1 in enumerate(shuffled_users):
            for j, user2 in enumerate(shuffled_users):
                if i < j:  # Avoid duplicates and self-pairs
                    # Calculate base compatibility score
                    base_score = self.calculate_match_score(user1, user2)
                    
                    # Apply history penalty if these users have met recently
                    history_weight = 0.0
                    if user1.id in history_graph and user2.id in history_graph[user1.id]:
                        history_weight = history_graph[user1.id][user2.id]
                    elif user2.id in history_graph and user1.id in history_graph[user2.id]:
                        history_weight = history_graph[user2.id][user1.id]
                    
                    # Calculate final score with history penalty
                    # Higher history weight = stronger penalty
                    final_score = base_score * (1.0 - (history_weight * HISTORY_PENALTY_FACTOR))
                    
                    # Store the score
                    pair_scores[(user1.id, user2.id)] = final_score
        
        # Create matches based on meeting size
        created_matches = []
        remaining_users = set(user.id for user in shuffled_users)
        
        # Log the matching process
        logger.info(f"Creating matches for {len(remaining_users)} users with meeting size {meeting_size}")
        
        while len(remaining_users) >= MIN_GROUP_SIZE:
            # For meeting size 2 (pairs), use pair scores directly
            if meeting_size == 2:
                # Find best available pair
                best_pair = None
                best_score = -1
                
                for (user1_id, user2_id), score in pair_scores.items():
                    if user1_id in remaining_users and user2_id in remaining_users and score > best_score:
                        best_pair = (user1_id, user2_id)
                        best_score = score
                
                if best_pair:
                    # Create match
                    match = await self._create_match([best_pair[0], best_pair[1]], scheduled_date)
                    created_matches.append(match)
                    
                    # Remove users from remaining pool
                    remaining_users.remove(best_pair[0])
                    remaining_users.remove(best_pair[1])
                    
                    logger.debug(f"Created pair match: {best_pair[0]} and {best_pair[1]} with score {best_score:.2f}")
                else:
                    # No valid pairs left
                    break
            else:
                # For larger meeting sizes, use a greedy algorithm to build optimal groups
                if not remaining_users:
                    break
                
                # Start with the two users who have the highest compatibility score
                best_initial_pair = None
                best_initial_score = -1
                
                for (user1_id, user2_id), score in pair_scores.items():
                    if user1_id in remaining_users and user2_id in remaining_users and score > best_initial_score:
                        best_initial_pair = (user1_id, user2_id)
                        best_initial_score = score
                
                if not best_initial_pair:
                    # Fall back to random selection if no good pair found
                    user_list = list(remaining_users)
                    if len(user_list) >= 2:
                        best_initial_pair = (user_list[0], user_list[1])
                    else:
                        break
                
                # Initialize group with the best pair
                current_group = list(best_initial_pair)
                for user_id in current_group:
                    remaining_users.remove(user_id)
                
                # Add users until we reach the meeting size or run out of users
                while len(current_group) < meeting_size and remaining_users:
                    best_next_user = None
                    best_avg_score = -1
                    
                    # Find the best next user to add based on average compatibility with current group
                    for user_id in remaining_users:
                        # Calculate average score with all current group members
                        total_score = 0
                        valid_pairs = 0
                        
                        for group_member in current_group:
                            pair = tuple(sorted([user_id, group_member]))
                            if pair in pair_scores:
                                score = pair_scores[pair]
                                total_score += score
                                valid_pairs += 1
                        
                        if valid_pairs > 0:
                            avg_score = total_score / valid_pairs
                            if avg_score > best_avg_score:
                                best_next_user = user_id
                                best_avg_score = avg_score
                    
                    if best_next_user:
                        current_group.append(best_next_user)
                        remaining_users.remove(best_next_user)
                        logger.debug(f"Added user {best_next_user} to group with avg score {best_avg_score:.2f}")
                    else:
                        break
                
                # Create match if we have enough users
                if len(current_group) >= MIN_GROUP_SIZE:
                    match = await self._create_match(current_group, scheduled_date)
                    created_matches.append(match)
                    logger.debug(f"Created group match with {len(current_group)} users")
                else:
                    # Put users back in the pool if group is too small
                    remaining_users.update(current_group)
        
        # Handle leftover users (if any)
        if remaining_users and len(remaining_users) >= MIN_GROUP_SIZE:
            # Create a match with the remaining users if there are at least MIN_GROUP_SIZE
            leftover_group = list(remaining_users)
            match = await self._create_match(leftover_group, scheduled_date)
            created_matches.append(match)
            logger.info(f"Created leftover match with {len(leftover_group)} users")
        elif remaining_users:
            # If we have leftover users but not enough for a new match,
            # add them to the smallest existing match
            if created_matches:
                # Find the smallest match
                smallest_match_index = 0
                smallest_match_size = len(created_matches[0].participants)
                
                for i, match in enumerate(created_matches):
                    if len(match.participants) < smallest_match_size:
                        smallest_match_index = i
                        smallest_match_size = len(match.participants)
                
                # Add leftover users to the smallest match
                leftover_users = list(remaining_users)
                updated_participants = created_matches[smallest_match_index].participants + leftover_users
                
                # Create a new match with the updated participants
                updated_match = await self._create_match(updated_participants, scheduled_date)
                
                # Replace the old match with the updated one
                created_matches[smallest_match_index] = updated_match
                logger.info(f"Added {len(leftover_users)} leftover users to existing match")
        
        return created_matches
    
    async def _create_match(self, participant_ids: List[str], scheduled_date: datetime) -> Match:
        """
        Create a match with the given participants.
        
        Args:
            participant_ids: List of participant user IDs
            scheduled_date: The scheduled date for the match
            
        Returns:
            The created match
        """
        match_create = MatchCreate(
            participants=participant_ids,
            scheduled_date=scheduled_date
        )
        
        match = Match(
            deployment_id=self.deployment_id,
            participants=match_create.participants,
            scheduled_date=match_create.scheduled_date
        )
        
        return await self.match_repository.create(match)