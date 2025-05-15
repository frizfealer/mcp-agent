"""
Unit tests for the UseCaseGenerator module.
"""

from unittest.mock import MagicMock, patch

# Temporarily disable logging for tests to keep output clean,
# or configure it to a test-specific level/handler.
# For simplicity here, disabling all logging from the module during tests.
# logging.disable(logging.CRITICAL)
from src.use_case_generator import UseCase, UseCaseGenerator, UseCaseResponse

# Ensure that if this test file is run directly, logging is configured.
# However, typically pytest or unittest runner handles this.
# from src.config import configure_logging
# configure_logging()


@patch("src.use_case_generator.get_llm_api_key")
@patch("src.use_case_generator.OpenAI")
def test_generate_use_cases_success(MockOpenAI, mock_get_llm_api_key):
    """
    Test successful generation of use cases.
    """
    mock_get_llm_api_key.return_value = "fake_api_key"
    mock_openai_instance = MockOpenAI.return_value
    mock_response = MagicMock()
    mock_response.output_parsed = UseCaseResponse(
        use_cases=[
            UseCase(id=1, title="User Registration", description="Users should be able to create a new account."),
            UseCase(id=2, title="User Login", description="Registered users should be able to log in."),
        ],
        reply="Here are the use cases.",
    )
    mock_openai_instance.responses.parse.return_value = mock_response

    generator = UseCaseGenerator()
    requirements = "User registration and login functionality."
    result = generator.generate_use_cases(requirements)

    assert result is not None
    assert isinstance(result, UseCaseResponse)
    assert len(result.use_cases) == 2
    assert result.use_cases[0].title == "User Registration"
    assert result.use_cases[1].id == 2
    assert result.reply == "Here are the use cases."
    mock_openai_instance.responses.parse.assert_called_once()


@patch("src.use_case_generator.get_llm_api_key")
def test_initialization_no_api_key(mock_get_llm_api_key):
    """
    Test UseCaseGenerator initialization when no API key is found.
    """
    mock_get_llm_api_key.return_value = None
    generator = UseCaseGenerator()
    assert generator.client is None
    result = generator.generate_use_cases("some requirements")
    assert result is None


@patch("src.use_case_generator.get_llm_api_key")
@patch("src.use_case_generator.OpenAI")
def test_generate_use_cases_empty_requirements(MockOpenAI, mock_get_llm_api_key):
    """
    Test generation with empty requirements text.
    """
    mock_get_llm_api_key.return_value = "fake_api_key"
    MockOpenAI.return_value
    generator = UseCaseGenerator()
    result = generator.generate_use_cases("   ")
    assert result is None
    # parse should not be called if requirements are empty
    assert not MockOpenAI.return_value.responses.parse.called


@patch("src.use_case_generator.get_llm_api_key")
@patch("src.use_case_generator.OpenAI")
def test_generate_use_cases_openai_api_error(MockOpenAI, mock_get_llm_api_key):
    """
    Test handling of an error from the OpenAI API.
    """
    mock_get_llm_api_key.return_value = "fake_api_key"
    mock_openai_instance = MockOpenAI.return_value
    mock_openai_instance.responses.parse.side_effect = Exception("OpenAI API Error")
    generator = UseCaseGenerator()
    result = generator.generate_use_cases("Valid requirements.")
    assert isinstance(result, UseCaseResponse)
    assert result.use_cases == []
    assert "couldn't generate use cases" in result.reply


@patch("src.use_case_generator.get_llm_api_key")
@patch("src.use_case_generator.OpenAI")
def test_generate_use_cases_pydantic_validation_error(MockOpenAI, mock_get_llm_api_key):
    """
    Test handling of Pydantic validation error due to malformed JSON from LLM.
    """
    mock_get_llm_api_key.return_value = "fake_api_key"
    mock_openai_instance = MockOpenAI.return_value
    # Simulate a pydantic validation error by raising an Exception
    mock_openai_instance.responses.parse.side_effect = Exception("Pydantic validation error")
    generator = UseCaseGenerator()
    result = generator.generate_use_cases("Valid requirements.")
    assert isinstance(result, UseCaseResponse)
    assert result.use_cases == []
    assert "couldn't generate use cases" in result.reply
