"""
MCP-Agent Main CLI Application
"""

import asyncio  # Added asyncio
import logging

from src.config import configure_logging
from src.flowchart_generator import FlowchartGenerator  # Added FlowchartGenerator
from src.input_parser import InputParser
from src.search_engine.search_manager import (  # Added SearchManager
    SearchManager,
)
from src.search_engine.sources.github_source import GitHubSource
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

        # Initialize FlowchartGenerator
        flowchart_generator = FlowchartGenerator()

        # 4. Initialize SearchManager
        github_source = GitHubSource()
        search_manager = SearchManager([github_source])

        # Process each use case
        for uc in use_cases_response.use_cases:
            print(f"\nProcessing Use Case: {uc.title} (ID: {uc.id})")
            print(f"Description: {uc.description}")

            # 4a. Generate Flowchart for the use case
            logger.info(f"Generating flowchart for use case: '{uc.title}'")
            flowchart_response = flowchart_generator.generate_flowchart(uc.description)

            if flowchart_response and flowchart_response.flowchart_mermaid_code:
                print(f"\n--- Flowchart for {uc.title} ---")
                if flowchart_response.reply:
                    print(f"Flowchart Description: {flowchart_response.reply}")
                print("```mermaid")
                print(flowchart_response.flowchart_mermaid_code)
                print("```")
                print("-----------------------------------\n")
            else:
                logger.warning(f"Could not generate flowchart for use case: {uc.title}")
                print(f"--- No Flowchart Generated for {uc.title} ---\n")

            # 4b. Search for MCPs/APIs for the use case
            logger.info(f"Searching for MCPs/APIs for use case: '{uc.title}'")
            search_query = f"{uc.title} {uc.description}\n Flowchart: {flowchart_response.flowchart_mermaid_code}"
            # Using title and description and flowchart for search
            found_mcps = await search_manager.search(search_query)

            if found_mcps:
                print(f"--- Found MCPs/APIs for Use Case: {uc.title} ---")
                for mcp_result in found_mcps:
                    print(f"  Name: {mcp_result.get('name', 'N/A')}")
                    print(f"  URL: {mcp_result.get('url', 'N/A')}")
                    description = mcp_result.get("description", "")
                    print(f"  Description: {description[:150]}..." if description else "N/A")
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
            print("====================================================\n")  # Separator for each use case block

    else:
        logger.warning("No use cases were generated, or an error occurred.")

    # ResultsFormatter is deferred. Output is handled directly above.
    logger.info("MCP-Agent processing complete.")


if __name__ == "__main__":
    asyncio.run(main())  # Run the async main function
