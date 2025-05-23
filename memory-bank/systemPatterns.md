# System Patterns: MCP-Agent

## 1. Architectural Overview

A modular architecture will be implemented in Python.

```mermaid
graph TD
    subgraph User Interfaces
        direction LR
        A_CLI[User Input (CLI via src/main.py)]
        A_GR[User Input (Web UI via src/gradio_app.py)]
    end

    A_CLI --> B(Input Parser);
    A_GR --> B;

    B[src/input_parser.py] -- Cleaned Text --> C[src/use_case_generator.py / LLM];
    C -- Structured Use Cases --> FCGEN[src/flowchart_generator.py / LLM];
    FCGEN -- Use Cases + Mermaid Flowcharts --> D_INPUT;

    subgraph Core Processing Logic
        style CoreProcessingLogic fill:#f9f,stroke:#333,stroke-width:1px
        D_INPUT[Use Case + Flowchart] --> D_SE[src/search_engine/ / MCP/API Search Engine];
        D_SE -- Found APIs & Details --> RES_OUT[Structured Results];
    end
    
    RES_OUT -- For CLI --> D_OUTPUT_CLI[Console Printing Logic in main.py];
    D_OUTPUT_CLI --> F_CLI[Output Display (Console)];

    RES_OUT -- For Web UI --> D_OUTPUT_GR[Markdown Formatting in gradio_app.py];
    D_OUTPUT_GR --> F_GR[Output Display (Gradio UI)];

    subgraph Core Logic & UI Modules (Python)
        B
        C
        FCGEN
        D_SE
        GR_APP[src/gradio_app.py]
        MAIN_APP[src/main.py]
        E[src/results_formatter.py (Deferred)]
    end

    C --> X[LLM API (External for UseCaseGenerator)];
    FCGEN --> X_FC[LLM API (External for FlowchartGenerator)];
    D_SE --> Z_GH_LLM[LLM API (External for GitHubSource)];
    D_SE --> Z_GH_API[GitHub API (for READMEs/Stars)];
    D_SE --> Z_GH_CACHE[Curated GitHub READMEs (Local Cache)];
    Z_GH_CACHE --> D_SE;

    F_CLI --> G_TERM[User's Terminal];
    F_GR --> G_BROWSER[User's Browser];
```

- **User Input Interfaces:**
  - **CLI (`src/main.py`):** A command-line interface where the user provides product requirements as text.
  - **Web UI (`src/gradio_app.py`):** A Gradio-based web interface for user input and results display.
- **Input Parser (`src/input_parser.py`):**
  - Receives raw text input.
  - Performs cleaning (whitespace, basic normalization).
  - Potentially segments text if too long for LLM context windows.
- **Use Case Generator / LLM Interaction (`src/use_case_generator.py`):**
  - Constructs a prompt using pre-defined templates and the cleaned requirements.
  - Sends the prompt to an external LLM API (e.g., OpenAI, Anthropic).
  - Receives and parses the LLM's response to extract structured use cases (Pydantic models).
  - Manages LLM API key via `src/config.py`.
- **Flowchart Generator / LLM Interaction (`src/flowchart_generator.py`):**
  - Takes a use case description.
  - Constructs a prompt for an LLM (e.g., OpenAI GPT series).
  - Sends the prompt to the LLM API to generate a Mermaid flowchart.
  - Receives and parses the LLM's response to extract a structured `FlowchartResponse` (Pydantic model) containing the Mermaid code.
  - Manages LLM API key via `src/config.py`.
- **MCP/API Search Engine (`src/search_engine/` package):**
  - Takes a use case description.
  - Formulates search queries.
  - Iterates through a configured, prioritized list of sources:
    - Specific MCP/API websites (e.g., `mcp.pipedream.com`, `mcpmarket.com`) (implementation deferred).
    - `GitHubSource` (`src/search_engine/sources/github_source.py`):
      - Maintains local cached copies of predefined GitHub README files (e.g., from `modelcontextprotocol/servers`, `punkpeye/awesome-mcp-servers`, `appcypher/awesome-mcp-servers`) located in `resources/github/`.
      - Updates these caches periodically if a `GITHUB_TOKEN` is available and files are older than one week.
      - Uses an LLM (e.g., `gpt-4.1-mini`) with a detailed system prompt to analyze the content of these cached files against the user's use case.
      - Extracts relevant sections from the Markdown (using `markdown-it-py`) for focused LLM analysis.
      - Optionally fetches GitHub stars for identified MCPs using the GitHub API.
    - General API directories or search engines as fallback if needed (implementation deferred).
  - Extracts MCP/API names, descriptions, links, and relevant metadata.
  - Implemented with sub-modules for each source type.
- **Results Formatter (`src/results_formatter.py`):** (Implementation Deferred)
  - Originally planned to take use cases, flowcharts, and MCP/API findings to generate a Markdown report.
  - Currently, output is handled directly in `src/main.py` (for CLI) and `src/gradio_app.py` (for Web UI).
- **Output Display:**
  - **Console (`src/main.py`):** The CLI script directly prints results to the console.
  - **Web UI (`src/gradio_app.py`):** The Gradio application formats results as Markdown and displays them in the user's web browser, including rendered Mermaid diagrams.

## 2. Key Technical Decisions & Patterns

- **Language:** Python.
- **Modularity:** Each component above will be a distinct Python module or package.
- **Configuration:** API keys, source URLs, and other configurations managed by `src/config.py` using `python-dotenv` and an `.env` file.
- **Asynchronous Operations:** `httpx` and `asyncio` will be used for concurrent network requests in the MCP/API Search Engine to improve performance.
- **Error Handling:** Standard Python `try-except` blocks within modules, with logging (`logging` module). Critical errors propagated to `main.py` for user notification.
- **Testing:** Unit tests in `tests/unit/` using `unittest` or `pytest`.
- **Dependency Management:** `requirements.txt` (includes `gradio` for the web UI).

## 3. Data Flow

**CLI Path (`src/main.py`):**

1. User provides requirements text via CLI.
2. `main.py` passes text to `InputParser`.
3. `InputParser` returns cleaned text.
4. `main.py` passes cleaned text to `UseCaseGenerator`.
5. `UseCaseGenerator` interacts with LLM API, returns a list of `UseCase` Pydantic objects.
6. `main.py` iterates through each `UseCase`:
    a. Passes the use case description to `FlowchartGenerator`.
    b. `FlowchartGenerator` interacts with LLM API, returns a `FlowchartResponse` Pydantic object.
    c. Passes the use case description (and flowchart) to `SearchEngine`.
    d. `SearchEngine` queries sources, returns findings.
    e. `main.py` prints results to the console.

**Web UI Path (`src/gradio_app.py`):**

1. User provides requirements text via Gradio Textbox.
2. `gradio_app.py`'s handler function receives the text.
3. The handler function passes text to `InputParser`.
4. `InputParser` returns cleaned text.
5. The handler passes cleaned text to `UseCaseGenerator`.
6. `UseCaseGenerator` interacts with LLM API, returns a list of `UseCase` Pydantic objects.
7. The handler iterates through each `UseCase`:
    a. Passes the use case description to `FlowchartGenerator`.
    b. `FlowchartGenerator` interacts with LLM API, returns a `FlowchartResponse` Pydantic object.
    c. Passes the use case description (and flowchart) to `SearchEngine`.
    d. `SearchEngine` queries sources, returns findings.
    e. The handler formats all results into a single Markdown string.
8. Gradio's `Markdown` component displays the formatted string in the browser.

`ResultsFormatter` is currently deferred for both paths.
