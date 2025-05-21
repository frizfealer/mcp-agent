"""
Contains the SearchManager class for orchestrating searches and the SearchResult model.
"""

import asyncio
from typing import Any, Dict, List

from src.search_engine.sources.base_source import BaseSourceHandler
from src.search_engine.sources.github_source import GitHubSource


class SearchManager:
    """
    Orchestrates the search process across various sources.
    """

    def __init__(self, source_handlers: List[BaseSourceHandler]):
        """
        Initializes the SearchManager with source handlers.
        Configuration is handled by individual components/handlers directly from src.config.
        """
        # self.config = get_config() # Removed as get_config() is not a general config provider
        self.source_handlers = source_handlers

    async def search(self, use_case_description: str) -> List[Dict[str, Any]]:
        """
        Performs a search for a given use case description across all configured sources.

        Args:
            use_case_description: The textual description of the use case.

        Returns:
            A list of SearchResult objects.
        """
        assert len(self.source_handlers) > 0, "No source handlers provided"

        tasks = [handler.search(use_case_description=use_case_description) for handler in self.source_handlers]

        results_from_all_sources = await asyncio.gather(*tasks, return_exceptions=True)
        all_results: List[Dict[str, Any]] = []
        for result_list in results_from_all_sources:
            if isinstance(result_list, list):
                all_results.extend(result_list)
            elif isinstance(result_list, Exception):
                # log.error(f"Error during search with a source handler: {result_list}")
                # Optionally, re-raise or handle more gracefully
                pass

        # TODO: Implement deduplication
        # TODO: Implement ranking/sorting if needed
        # TODO: Implement limiting results based on config.SEARCH_TOTAL_RESULT_LIMIT
        return all_results


if __name__ == "__main__":
    import asyncio

    from src.search_engine.sources.github_source import GitHubSource

    async def main_test():
        github_handler = GitHubSource()
        manager = SearchManager([github_handler])

        test_use_case = "A system to manage customer orders and track shipments."
        results = await manager.search(test_use_case)

        if results:
            print(f"\nFound {len(results)} results for use case: '{test_use_case}'")
            for res in results:
                for k, v in res.items():
                    print(f"{k}: {v}")
                print("\n")
        else:
            print(f"No results found for use case: '{test_use_case}'")

    asyncio.run(main_test())
