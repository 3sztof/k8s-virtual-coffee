"""
Base repository interface for data access abstraction.
"""
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(Generic[T], ABC):
    """
    Base repository interface for data access abstraction.
    """

    @abstractmethod
    async def create(self, item: T) -> T:
        """
        Create a new item.

        Args:
            item: The item to create

        Returns:
            The created item
        """

    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """
        Get an item by ID.

        Args:
            id: The ID of the item to get

        Returns:
            The item if found, None otherwise
        """

    @abstractmethod
    async def get_all(self, filter_params: Optional[dict[str, Any]] = None) -> list[T]:
        """
        Get all items, optionally filtered.

        Args:
            filter_params: Optional filter parameters

        Returns:
            A list of items
        """

    @abstractmethod
    async def update(self, id: str, item: T) -> Optional[T]:
        """
        Update an item.

        Args:
            id: The ID of the item to update
            item: The updated item

        Returns:
            The updated item if found, None otherwise
        """

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete an item.

        Args:
            id: The ID of the item to delete

        Returns:
            True if the item was deleted, False otherwise
        """
