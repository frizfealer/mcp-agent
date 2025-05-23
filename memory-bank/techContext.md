# Tech Context: MCP-Agent

## 1. Key Technologies

- **Primary Programming Language:** Python (version 3.8+ recommended for `asyncio` features and library compatibility).
- **LLM Integration:**
  - **Choice of LLM:** OpenAI's GPT series (e.g., `gpt-4.1-mini`) is used by `UseCaseGenerator`, `FlowchartGenerator`, and `GitHubSource`. The system requires an `OPENAI_API_KEY`.
  - **Python LLM Client Libraries:**
    - `openai` (used by `UseCaseGenerator`, `FlowchartGenerator`, and `GitHubSource`).
    - `instructor` (used with `openai` client for Pydantic model responses in `UseCaseGenerator` and `FlowchartGenerator`).
    - `anthropic` (option for future if Anthropic models are used).
    - Generic HTTP library like `httpx` (option for other LLM APIs).
- **Web Interaction & Scraping (for MCP/API Search):**
  - **HTTP Client:** `httpx` (for robust synchronous and asynchronous HTTP requests, potentially by future web scraping sources).
  - **HTML/XML Parsing:** `BeautifulSoup4` (with `lxml` parser for performance, for potential future web scraping sources).
  - **GitHub API Client:** `PyGithub` (used by `GitHubSource` for fetching READMEs if cache is stale and for fetching star counts).
  - **Apify SDK:** `apify-client` (Python) if using Apify platform/actors (for potential future sources).
- **Markdown Processing:**
  - `markdown-it-py` (used by `GitHubSource` for parsing cached GitHub READMEs to extract specific sections).
- **UI Framework:**
  - `gradio` (for building the web UI).
- **Environment Variable Management:**
  - `python-dotenv` (to load environment variables from an `.env` file).
- **Testing Framework:**
  - `pytest` (recommended for its flexibility and rich feature set).
  - `unittest` (standard library, also an option).
- **Logging:**
  - Python's built-in `logging` module.
- **CLI Argument Parsing:**
  - `argparse` (standard library) or `Typer`/`Click` (for more sophisticated CLIs). Initially, `argparse` might suffice.

## 2. Development Environment & Project Structure

- **Project Root:** `/Users/yeu-chernharn/repos/mcp_agent` (current working directory).
  - `src/`: Contains all application source code.
    - `__init__.py`
    - `main.py`: Main CLI entry point.
    - `gradio_app.py`: Gradio Web UI application.
    - `config.py`: Loads and provides access to configuration (API keys, source URLs).
    - `input_parser.py`
    - `use_case_generator.py`
    - `flowchart_generator.py`
    - `search_engine/`
      - `__init__.py`
      - `search_manager.py`
      - `sources/` (e.g., `github.py`, `pipedream.py`, `generic_web.py`)
    - `results_formatter.py` (Implementation Deferred)
    - `utils.py` (optional, for shared utilities)
  - `tests/`: Contains all tests.
    - `unit/`: For unit tests.
    - `integration/` (optional, for integration tests later).
  - `memory-bank/`: Contains these documentation files.
  - `.env`: For storing API keys (e.g., `OPENAI_API_KEY`, `GITHUB_TOKEN`). (This file will be in `.gitignore`).
  - `requirements.txt`: Lists Python package dependencies.
  - `.gitignore`: Specifies intentionally untracked files by Git (e.g., `.env`, `__pycache__/`, `*.pyc`, virtual environment directories).
  - `README.md`: Project-level README with setup and usage instructions.

## 3. Technical Constraints & Considerations

- **Internet Access:** Required for LLM API calls and querying web sources.
- **API Keys:** Valid API keys needed for LLM service and GitHub (for higher rate limits).
- **Rate Limiting:** Implement respectful request rates and backoff strategies for all external services.
- **Prompt Engineering:** Significant effort required to create effective prompts for the LLM to extract use cases accurately and generate valid Mermaid flowcharts.
- **Scraping Reliability:** Web scraping is prone to breakage if website structures change. Prioritize official APIs where available.
- **Asynchronous Design:** Crucial for performance due to I/O-bound nature of network requests. `asyncio` and `httpx` are key.
- **Error Handling:** Robust error handling for network issues, API errors, parsing failures, and unexpected data.
- **Security:** Ensure API keys are not hardcoded or committed to version control. Use `.env` and `.gitignore`.
- **Python Version:** Ensure consistency, e.g., by specifying in `README.md` or using tools like `pyenv`.
