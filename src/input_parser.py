import logging

logger = logging.getLogger(__name__)


class InputParser:
    """
    Parses and cleans the raw text input provided by the user.
    """

    def parse(self, raw_text: str) -> str:
        """
        Performs basic cleaning of the input text.

        Args:
            raw_text: The raw string input from the user.

        Returns:
            The cleaned text.
        """
        if not isinstance(raw_text, str):
            raise TypeError("Input text must be a string.")

        cleaned_text = raw_text.strip()
        # Future enhancements:
        # - More sophisticated whitespace normalization (e.g., multiple spaces to one)
        # - Text segmentation for very long inputs
        # - Basic grammar/spelling correction (optional, might be out of scope)
        return cleaned_text


if __name__ == "__main__":
    # Example usage (for testing purposes)
    parser = InputParser()
    sample_input_empty = ""
    sample_input_spaces = "   Hello, world!   "
    sample_input_normal = "This is a normal sentence."

    logger.info(f"Input: '{sample_input_empty}' -> Parsed: '{parser.parse(sample_input_empty)}'")
    logger.info(f"Input: '{sample_input_spaces}' -> Parsed: '{parser.parse(sample_input_spaces)}'")
    logger.info(f"Input: '{sample_input_normal}' -> Parsed: '{parser.parse(sample_input_normal)}'")

    try:
        parser.parse(123)  # type: ignore
    except TypeError as e:
        print(f"Error with non-string input: {e}")
