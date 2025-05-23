"""
Configuration loader for MCP-Agent.
Loads API keys and other settings from .env file.

This module configures logging globally for the application. It should be imported at the start of your main application (e.g., in main.py) to ensure logging is set up for all modules that use logging.
"""

import logging
import os

from dotenv import load_dotenv


def configure_logging():
    """
    Configures logging with atime in the format and sets default log level to INFO.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


logger = logging.getLogger(__name__)

# Load environment variables from .env file
# First try the Cloud Run mounted path, then fall back to default behavior
cloud_run_env_path = "/secrets/.env"
if os.path.exists(cloud_run_env_path):
    logger.info(f"Loading environment from Cloud Run mounted file: {cloud_run_env_path}")
    load_dotenv(dotenv_path=cloud_run_env_path, override=True)
else:
    logger.info("Loading environment from local .env file")
    # Looks for .env in the current directory or parent directories
    load_dotenv(override=True)

# --- LLM Configuration ---
# Example: OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# User will need to set their specific LLM API key and potentially other LLM settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Generic name, user to replace with specific e.g. OPENAI_API_KEY
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "default-model")  # Example, if model can be configured

# --- GitHub Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- Search Engine Configuration ---
# List of prioritized sources for MCP/API search
# This can be expanded with more details per source (e.g., specific paths, selectors if scraping)
MCP_SOURCE_URLS = {
    "pipedream": "https://mcp.pipedream.com/?q=",  # Query parameter based
    "mcpmarket": "https://mcpmarket.com/",  # Needs investigation for search mechanism
    "pulsemcp": "https://www.pulsemcp.com/servers",  # Directory
    "opentools": "https://opentools.com/registry",  # Directory
    "apify": "https://apify.com/",  # Platform, might use its API or specific actors
    "github_modelcontextprotocol_servers": "https://github.com/modelcontextprotocol/servers",
    "github_awesome_mcp_servers": "https://github.com/punkpeye/awesome-mcp-servers",
}

# Specific repositories to search within (e.g., for targeted MCP server lists)
# User can add to this list in their .env file by providing a comma-separated string
# e.g., GITHUB_REPOSITORIES_TO_SEARCH="org1/repo1,org2/repo2"
_github_repos_env = os.getenv("GITHUB_REPOSITORIES_TO_SEARCH", "")
GITHUB_REPOSITORIES_TO_SEARCH: list[str] = (
    [repo.strip() for repo in _github_repos_env.split(",") if repo.strip()] if _github_repos_env else []
)

# Default limit for results per search source
try:
    SEARCH_RESULT_LIMIT_PER_SOURCE = int(os.getenv("SEARCH_RESULT_LIMIT_PER_SOURCE", "5"))
except ValueError:
    logger.warning(
        f"Invalid value for SEARCH_RESULT_LIMIT_PER_SOURCE: '{os.getenv('SEARCH_RESULT_LIMIT_PER_SOURCE')}'. "
        f"Defaulting to 5."
    )
    SEARCH_RESULT_LIMIT_PER_SOURCE = 5

# Enabled search sources, comma-separated in .env, e.g., "github,pipedream"
_search_sources_env = os.getenv("SEARCH_SOURCES_ENABLED", "github")  # Default to github
SEARCH_SOURCES_ENABLED: list[str] = [
    source.strip().lower() for source in _search_sources_env.split(",") if source.strip()
]


# --- Other Configurations ---
# Example: LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def get_LLM_model_name() -> str:
    """Returns the configured LLM model name."""
    if not LLM_MODEL_NAME:
        logger.warning("LLM_MODEL_NAME is not set in .env file. Using default.")
    return LLM_MODEL_NAME or "default-model"  # Ensure a string is returned


def get_llm_api_key() -> str | None:
    """Returns the configured LLM API key."""
    if not OPENAI_API_KEY:
        # Consider raising an error or returning a default/None and handling in the calling code
        logger.warning("OPENAI_API_KEY is not set in .env file.")
    return OPENAI_API_KEY


def get_github_token() -> str | None:
    """Returns the configured GitHub token."""
    if not GITHUB_TOKEN:
        logger.info("GITHUB_TOKEN is not set in .env file. GitHub API calls may be rate-limited.")
    return GITHUB_TOKEN


# Add more getter functions as needed for other configurations

if __name__ == "__main__":
    # For testing and displaying loaded configs
    configure_logging()  # Ensure logging is configured if run directly
    logger.info(f"LLM API Key Loaded: {'Yes' if get_llm_api_key() else 'No'}")
    logger.info(f"LLM Model Name: {get_LLM_model_name()}")
    logger.info(f"GitHub Token Loaded: {'Yes' if get_github_token() else 'No'}")
    logger.info(f"MCP Sources: {MCP_SOURCE_URLS}")
    logger.info(f"GitHub Repositories to Search: {GITHUB_REPOSITORIES_TO_SEARCH}")
    logger.info(f"Search Result Limit Per Source: {SEARCH_RESULT_LIMIT_PER_SOURCE}")
    logger.info(f"Search Sources Enabled: {SEARCH_SOURCES_ENABLED}")
