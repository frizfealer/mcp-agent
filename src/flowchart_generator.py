import logging
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from src.config import OPENAI_API_KEY, configure_logging

# Configure logging if this module is run directly (for testing)
if __name__ != "__main__":  # Only configure if not main, main.py will configure
    pass  # In a real app, main.py or an entry script handles global config
else:  # If run as main script for testing
    configure_logging()

logger = logging.getLogger(__name__)


class FlowchartResponse(BaseModel):
    """
    Represents the structured response for a generated flowchart.
    """

    flowchart_mermaid_code: str = Field(
        ..., description="The Mermaid code representing the flowchart for the use case."
    )
    reply: str = Field(..., description="A reply to the user's along with the flowchart_mermaid_code.")


MODEL_NAME = "gpt-4.1"

SYSTEM_PROMPT = """
Generate a concise and clear Mermaid flowchart (graph TD) from a provided use case description. The flowchart should highlight the main steps, actors, and interactions in the use case with a focus on clarity and simplicity. Ensure the Mermaid syntax is correct.

# Steps

1. Analyze the use case description to identify main steps, actors, and interactions.
2. Translate these elements into a sequence of nodes and links within a Mermaid flowchart.
3. Use correct Mermaid syntax to represent the flowchart as graph TD.
4. Follow the output format strictly.

# Examples

**Example Input:**

"Use case: User purchases a book from an online store. User selects a book, adds to cart, proceeds to checkout, enters payment information, and confirms the purchase. System processes the order and sends a confirmation email."

**Example Output (A FlowchartResponse pydantic model):**
flowchart_mermaid_code:
```mermaid
flowchart LR
    A[User] --> B[Selects Book]
    B --> C[Adds to Cart]
    C --> D[Proceeds to Checkout]
    D --> E[Enters Payment Information]
    E --> F[Confirms Purchase]
    F --> G[System Processes Order]
    G --> H[Sends Confirmation Email]
```
reply:
"Here is the flowchart for the use case."
"""


class FlowchartGenerator:
    """
    Generates a Mermaid flowchart for a given use case using an LLM.
    """

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required for FlowchartGenerator.")

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"FlowchartGenerator initialized with model: {MODEL_NAME}")

    def generate_flowchart(self, use_case_description: str) -> Optional[FlowchartResponse]:
        """
        Generates a Mermaid flowchart for the provided use case description.

        Args:
            use_case_description: The textual description of the use case.

        Returns:
            A FlowchartResponse object containing the Mermaid code, or None if generation fails.
        """
        if not use_case_description:
            logger.warning("Use case description is empty. Cannot generate flowchart.")
            return None

        user_prompt = (
            f"Generate a Mermaid flowchart (flowchart TD) for the following use case:\n\n"
            f"'{use_case_description}'\n\n"
        )

        try:
            logger.info(f"Generating flowchart for use case: '{use_case_description[:100]}...'")
            response = self.client.responses.parse(
                model=MODEL_NAME,
                text_format=FlowchartResponse,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,  # Lower temperature for more deterministic flowchart structure
            )
            logger.info(f"Successfully generated flowchart for use case: '{use_case_description[:100]}...'")
            return response.output_parsed
        except Exception as e:
            logger.error(
                f"Error generating flowchart for use case '{use_case_description[:100]}...': {e}", exc_info=True
            )
            return None


if __name__ == "__main__":
    # Basic test (requires .env file with OPENAI_API_KEY)

    generator = FlowchartGenerator()
    sample_use_case = "A user logs into the system, uploads a CSV file. The system parses the file, validates the data, stores it in a database, and then sends an email notification to the administrator about the successful upload."

    flowchart_data = generator.generate_flowchart(sample_use_case)

    if flowchart_data:
        print("\n--- Generated Flowchart ---")
        print(f"Description: {flowchart_data.reply}")
        print("Mermaid Code:")
        print(f"```mermaid\n{flowchart_data.flowchart_mermaid_code}\n```")
    else:
        print("\nFailed to generate flowchart.")

    sample_use_case_2 = "The system monitors a directory for new image files. When a new image appears, it's automatically resized to a thumbnail, watermarked, and uploaded to cloud storage. A record of the image and its cloud URL is saved in the database."
    flowchart_data_2 = generator.generate_flowchart(sample_use_case_2)
    if flowchart_data_2:
        print("\n--- Generated Flowchart 2 ---")
        print(f"Description: {flowchart_data_2.reply}")
        print("Mermaid Code:")
        print(f"```mermaid\n{flowchart_data_2.flowchart_mermaid_code}\n```")
