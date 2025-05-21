# Active Context: MCP-Agent

## 1. Current Focus

- Preparing for next iteration (implementing web scraping source handlers).
- Updating Memory Bank documentation.
- (Current iteration's Search Engine integration work is complete).

## 2. Recent Achievements & Decisions

- Successfully implemented the `UseCaseGenerator` module (`src/use_case_generator.py`) using OpenAI's JSON mode and Pydantic models for structured output.
- Developed comprehensive unit tests for `UseCaseGenerator` (`tests/unit/test_use_case_generator.py`), ensuring its reliability.
- Integrated `UseCaseGenerator` into `src/main.py`, allowing it to process user input and display generated use cases.
- Agreed on the core Memory Bank file structure and initial content.
- Confirmed Python as the primary programming language.
- Decided on a project structure (`src/`, `tests/unit/`) and `python-dotenv` for environment variables.
- Outlined the MCP-agent architecture: Input Parser, LLM-based Use Case Generator, MCP/API Search Engine (with specific sources), Results Formatter (Markdown), and Console Output.
- Reviewed and confirmed the initial implementations for user input (`src/main.py`), input parsing (`src/input_parser.py`), and logging/configuration (`src/config.py`) are sensible and provide a good foundation.
- Successfully scaffolded the `SearchEngine` module (`src/search_engine/`) including `SearchManager`, `SearchResult` model, `BaseSourceHandler`, and placeholder source handlers.
- Updated unit tests for `src/main.py` to cover current functionality.
- Developed initial unit tests for `SearchManager` (`tests/unit/test_search_manager.py`).
- Implemented an advanced `GitHubSource` (`src/search_engine/sources/github_source.py`). This version utilizes an LLM (e.g., `gpt-4.1-mini`) to analyze curated lists of MCPs from specific GitHub repositories (`modelcontextprotocol/servers`, `punkpeye/awesome-mcp-servers`, `appcypher/awesome-mcp-servers`). It includes:
  - Local caching of these README files in `resources/github/`.
  - Dynamic updates to the cache if a `GITHUB_TOKEN` is provided and files are older than a week.
  - Extraction of specific sections from Markdown for focused LLM analysis.
  - Fetching of GitHub stars for identified MCP candidates.
- Developed unit tests for the enhanced `GitHubSource` (`tests/unit/test_github_source.py`).
- Added `GITHUB_REPOSITORIES_TO_SEARCH` (now implicitly `GITHUB_CACHE_PATHS`), `SEARCH_RESULT_LIMIT_PER_SOURCE`, and `SEARCH_SOURCES_ENABLED` to `src/config.py`, which are utilized by `GitHubSource` and `SearchManager`.
- Confirmed `_initialize_source_handlers` in `SearchManager` correctly loads and operates with the enhanced `GitHubSource` based on `SEARCH_SOURCES_ENABLED`.
- Integrated `SearchManager.search()` into `src/main.py`, confirming its asynchronous operation and capability to search for MCPs/APIs for each use case using the advanced `GitHubSource`.

## 3. Next Steps (Implementation Phase)

- (Deferred to next iteration: Implement `PipedreamMCPSource` (web scraping) and its unit tests).
- (Deferred to next iteration: Implement `MCPMarketSource` (web scraping) and its unit tests).
- (Deferred to next iteration: Update `_initialize_source_handlers` in `SearchManager` to load these new handlers).
- Implement `ResultsFormatter` module.
- Integrate `ResultsFormatter` into `src/main.py`.
- Develop unit tests for `ResultsFormatter`.
- Update `progress.md` to reflect these advancements.

## 4. Key Considerations & Learnings

- LLM prompt engineering is crucial for both the `UseCaseGenerator` and the `GitHubSource` (specifically its detailed system prompt for analyzing curated lists).
- Robust interaction with diverse external data sources for the MCP/API Search Engine remains complex. The `GitHubSource` now also depends on the structure and specific section headings (e.g., "servers", "Server Implementations") within the curated GitHub READMEs for optimal functionality.
- Asynchronous operations are vital for performance, as demonstrated in `SearchManager` and `GitHubSource`.
- Auto-formatting by the editor needs to be considered for future file modifications (SEARCH/REPLACE blocks).
