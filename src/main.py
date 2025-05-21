"""
MCP-Agent Main CLI Application
"""

import asyncio  # Added asyncio
import logging

from src.config import configure_logging
from src.input_parser import InputParser
from src.search_engine.search_manager import (  # Added SearchManager
    SearchManager,
)
from src.search_engine.sources.github_source import GitHubSource  # Import GitHubSource
from src.use_case_generator import UseCaseGenerator

configure_logging()

logger = logging.getLogger(__name__)


def get_user_requirements() -> str:
    """
    Prompts the user to enter their product requirements.
    Allows for multi-line input.
    """
    print("Please enter your product requirements. Press Enter twice to finish.")
    lines = []
    while True:
        try:
            line = input()
            if not line:  # Empty line signifies end of input
                break
            lines.append(line)
        except EOFError:  # Handles Ctrl+D or end of piped input
            break
    return "\n".join(lines)


async def main():  # Changed to async def
    """
    Main function to run the MCP-Agent.
    """
    logger.info("MCP-Agent starting...")

    # 1. Get user input (product requirements)
    raw_requirements = get_user_requirements()

    if not raw_requirements.strip():
        logger.exception("No input received. Exiting.")
        return

    # 2. Call InputParser
    parser = InputParser()
    try:
        cleaned_requirements = parser.parse(raw_requirements)
        print("\n--- Cleaned Requirements ---")
        print(cleaned_requirements)
        print("--------------------------\n")
    except TypeError as e:
        logger.exception(f"Error processing input: {e}")
        return

    # 3. Call UseCaseGenerator
    use_case_generator = UseCaseGenerator()
    use_cases_response = use_case_generator.generate_use_cases(cleaned_requirements)

    if use_cases_response and use_cases_response.use_cases:
        print(f"Reply from UseCaseGenerator: {use_cases_response.reply}")
        print("\n--- Generated Use Cases ---")
        for uc in use_cases_response.use_cases:
            print(f"  ID: {uc.id}")
            print(f"  Title: {uc.title}")
            print(f"  Description: {uc.description}")
            print("  " + "-" * 20)
        print("--------------------------\n")

        # 4. Initialize SearchManager and search for each use case
        github_source = GitHubSource()
        search_manager = SearchManager([github_source])
        all_found_mcps: dict[int, list[dict]] = {}

        for uc in use_cases_response.use_cases:
            logger.info(f"Searching for MCPs/APIs for use case: '{uc.title}'")
            # Construct a query for the search engine, could be title + description
            search_query = f"{uc.title} {uc.description}"
            found_mcps = await search_manager.search(search_query)  # Await the async search
            all_found_mcps[uc.id] = found_mcps

            if found_mcps:
                print(f"\n--- Found MCPs/APIs for Use Case: {uc.title} ---")
                for mcp_result in found_mcps:
                    print(f"  Name: {mcp_result.get('name', '')}")
                    print(f"  URL: {mcp_result.get('url', '')}")
                    print(f"  Description: {mcp_result.get('description', '')[:100]}...")  # Print snippet
                    if mcp_result.get("corresponding_functions"):
                        print(f"  Functions: {mcp_result['corresponding_functions']}")
                    if mcp_result.get("reasoning"):
                        print(f"  Reasoning: {mcp_result['reasoning']}")
                    if mcp_result.get("stars") is not None:
                        print(f"  Stars: {mcp_result['stars']}")
                    print("  " + "." * 20)
                print("--------------------------------------------------\n")
            else:
                print(f"No MCPs/APIs found for use case: {uc.title}\n")
    else:
        logger.warning("No use cases were generated, or an error occurred.")

    # TODO:
    # 5. Call ResultsFormatter (when implemented)
    # 6. Print formatted results (when implemented)
    logger.info("MCP-Agent processing complete.")


if __name__ == "__main__":
    asyncio.run(main())  # Run the async main function
