# src/search_engine/sources/base_source.py
"""
Defines the abstract base class for all source handlers.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseSourceHandler(ABC):
    """
    Abstract base class for source handlers.
    Each handler is responsible for searching one specific type of source.
    Individual handlers will fetch necessary config values directly from src.config.
    """

    def __init__(self, source_name: str):
        """
        Initializes the source handler.

        Args:
            source_name: A string name for this source (e.g., "GitHub", "Pipedream").
        """
        # self.config = config # Removed, handlers get their own config
        self.source_name = source_name
        # Potentially initialize httpx client here if shared across all handlers
        # self.http_client = httpx.AsyncClient()

    @abstractmethod
    async def search(self, use_case_description: str) -> List[Dict[str, Any]]:
        """
        Performs a search for a given query related to a use case.

        Args:
            query: The search query string (can be the use case description itself
                   or a transformed version).
            use_case_description: The original use case description, for context.

        Returns:
            A list of SearchResult objects found by this source.
            Should return an empty list if no results are found or an error occurs.
        """
        pass

    # Optional: Add a method to close resources like httpx client if created per handler
    # async def close(self):
    #     if hasattr(self, 'http_client'):
    #         await self.http_client.aclose()
