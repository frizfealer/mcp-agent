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
# Looks for .env in the current directory or parent directories
load_dotenv()

# --- LLM Configuration ---
# Example: OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# User will need to set their specific LLM API key and potentially other LLM settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Generic name, user to replace with specific e.g. OPENAI_API_KEY
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "default-model")  # Example, if model can be configured

# --- GitHub Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optional, but recommended for higher rate limits

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

# --- Other Configurations ---
# Example: LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def get_LLM_model_name():
    """Returns the configured LLM model name."""
    if not LLM_MODEL_NAME:
        print("Warning: LLM_MODEL_NAME is not set in .env file.")
    return LLM_MODEL_NAME


def get_llm_api_key():
    """Returns the configured LLM API key."""
    if not OPENAI_API_KEY:
        # Consider raising an error or returning a default/None and handling in the calling code
        print("Warning: OPENAI_API_KEY is not set in .env file.")
    return OPENAI_API_KEY


def get_github_token():
    """Returns the configured GitHub token."""
    if not GITHUB_TOKEN:
        print("Info: GITHUB_TOKEN is not set in .env file. GitHub API calls may be rate-limited.")
    return GITHUB_TOKEN


# Add more getter functions as needed for other configurations

if __name__ == "__main__":
    # For testing an_github_token = get_github_token()d displaying loaded configs
    logger.info(f"LLM API Key Loaded: {'Yes' if OPENAI_API_KEY else 'No'}")
    logger.info(f"LLM Model Name: {LLM_MODEL_NAME}")
    logger.info(f"GitHub Token Loaded: {'Yes' if GITHUB_TOKEN else 'No'}")
    logger.info(f"MCP Sources: {MCP_SOURCE_URLS}")
