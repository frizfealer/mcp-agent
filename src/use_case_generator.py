"""
UseCaseGenerator Module

This module is responsible for taking cleaned product requirements text
and generating a list of use cases using an LLM (e.g., OpenAI).
It leverages OpenAI's JSON mode for structured output.
"""

import logging
from typing import List, Optional

from openai import OpenAI
from pydantic import BaseModel

from src.config import configure_logging, get_llm_api_key

# Configure logging if this module is run directly (for testing)
if __name__ != "__main__":  # Only configure if not main, main.py will configure
    pass  # In a real app, main.py or an entry script handles global config
else:  # If run as main script for testing
    configure_logging()


logger = logging.getLogger(__name__)

# --- Pydantic Models for Structured Output ---


class UseCase(BaseModel):
    """
    Represents a single use case with an ID, title, and description.
    """

    id: int
    title: str
    description: str


class UseCaseResponse(BaseModel):
    """
    Represents the expected JSON structure from the LLM, containing a list of use cases.
    """

    use_cases: List[UseCase]
    reply: str


# --- UseCaseGenerator Class ---

MODEL_NAME = "gpt-4.1"


class UseCaseGenerator:
    """
    Generates use cases from product requirements text using an LLM.
    """

    def __init__(self):
        """
        Initializes the UseCaseGenerator with an OpenAI client.
        """
        self.api_key = get_llm_api_key()
        if not self.api_key:
            logger.error("OpenAI API key not found. Please set it in the .env file.")
            # In a real application, this might raise an exception or have a clearer startup failure.
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
        self.model_name = MODEL_NAME
        logger.info("UseCaseGenerator initialized.")

    def generate_use_cases(self, requirements_text: str) -> Optional[UseCaseResponse]:
        """
        Generates use cases from the given requirements text using OpenAI's chat completions.

        Args:
            requirements_text: The cleaned product requirements text.

        Returns:
            A UseCaseResponse object containing the list of use cases, or None if an error occurs.
        """
        if not self.client:
            logger.error("OpenAI client not initialized due to missing API key.")
            return None

        if not requirements_text.strip():
            logger.warning("Requirements text is empty. Cannot generate use cases.")
            return None

        # This is a placeholder prompt. Significant prompt engineering will be needed.
        system_prompt = (
            "You are an expert product analyst. Your task is to identify and extract distinct "
            "use cases from the provided product requirements. For each use case, provide a concise "
            "title and a brief description."
        )
        user_prompt = f"Here are the product requirements:\n\n{requirements_text}"

        try:
            logger.info("Sending request to OpenAI API for use case generation...")
            response = self.client.responses.parse(
                model=self.model_name,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text_format=UseCaseResponse,
            )

            parsed_response = response.output_parsed
            return parsed_response

        except Exception as e:
            logger.error(f"An unexpected error occurred while calling OpenAI API: {e}")
            response = UseCaseResponse(use_cases=[], reply="Sorry, I couldn't generate use cases for this.")
            return response


if __name__ == "__main__":
    # This is a basic test. Requires OPENAI_API_KEY in .env
    # Ensure configure_logging() is called if you run this directly.
    # (It's called at the top of this file if __name__ == "__main__")

    logger.info("Testing UseCaseGenerator...")
    generator = UseCaseGenerator()

    if generator.client:  # Proceed only if client initialized (API key was found)
        sample_requirements = """
        The application should allow users to register for an account using their email and password.
        Once registered, users should be able to log in.
        Logged-in users can create new projects, specifying a project name and description.
        Users should also be able to view a list of their projects and delete projects they own.
        """

        use_case_data = generator.generate_use_cases(sample_requirements)

        if use_case_data:
            print(f"Reply: {use_case_data.reply}")
            print("\n--- Generated Use Cases ---")
            for uc in use_case_data.use_cases:
                print(f"  ID: {uc.id}")
                print(f"  Title: {uc.title}")
                print(f"  Description: {uc.description}")
                print("-" * 10)
        else:
            print("Failed to generate use cases from sample requirements.")
    else:
        print("OpenAI client could not be initialized. Check API key in .env file.")
