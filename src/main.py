"""
MCP-Agent Main CLI Application
"""

import logging

from src.config import configure_logging
from src.input_parser import InputParser
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


def main():
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
        print(f"Reply: {use_cases_response.reply}")
        print("\n--- Generated Use Cases ---")
        for uc in use_cases_response.use_cases:
            print(f"  ID: {uc.id}")
            print(f"  Title: {uc.title}")
            print(f"  Description: {uc.description}")
            print("  " + "-" * 20)
        print("--------------------------\n")
    else:
        logger.warning("No use cases were generated, or an error occurred.")

    # TODO: Implement remaining workflow:
    # 4. Loop through use cases:
    #    a. Call SearchEngine
    # 5. Call ResultsFormatter
    # 6. Print formatted results
    logger.info("MCP-Agent finished (Use Case Generation step complete).")


if __name__ == "__main__":
    main()
