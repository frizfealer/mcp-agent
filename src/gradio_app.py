"""
Gradio Web UI for MCP-Agent
"""

import asyncio
import logging
import os

import gradio as gr

from src.config import configure_logging
from src.flowchart_generator import FlowchartGenerator
from src.input_parser import InputParser
from src.search_engine.search_manager import SearchManager
from src.search_engine.sources.github_source import (
    GitHubSource,  # Assuming direct instantiation
)
from src.use_case_generator import UseCaseGenerator

# Configure logging once when the module is loaded
configure_logging()
logger = logging.getLogger(__name__)

# Initialize components once
input_parser = InputParser()
use_case_generator = UseCaseGenerator()
flowchart_generator = FlowchartGenerator()
github_source = GitHubSource()
search_manager = SearchManager([github_source])

MAX_TABS = 10

MERMAID_LOADER = """
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({ startOnLoad: false });
  window._mermaid = mermaid;
</script>
"""
# Mermaid re-render trigger script (runs every time user updates)
MERMAID_TRIGGER = """
<script>
  async function renderMermaid() {
    const blocks = document.querySelectorAll('.prose pre code.language-mermaid');
    if (!blocks.length || !window._mermaid) return;

    for (const block of blocks) {
      const code = block.textContent;
      const container = document.createElement("div");
      container.className = "mermaid";
      container.textContent = code;
      block.closest("pre").replaceWith(container);
    }
    try {
      await window._mermaid.run();
    } catch (e) {
      console.error("Mermaid rendering error:", e);
    }
  }
  requestAnimationFrame(renderMermaid);
</script>
"""


def process_requirements_gradio(raw_requirements_text: str):
    logger.info("Gradio app processing request...")

    # Initialize the state for all potential outputs (tabs and their markdown contents)
    # Each tab update + markdown update = 2 entries in current_outputs_state
    current_outputs_state = []
    for i in range(MAX_TABS):
        current_outputs_state.append(gr.update(visible=False, label=f"UC {i + 1}"))  # Tab update object
        current_outputs_state.append(gr.update(value=""))  # Markdown update object

    # Initial yield to set all tabs to hidden and clear content
    yield *current_outputs_state, MERMAID_TRIGGER

    if not raw_requirements_text.strip():
        logger.warning("No input received from Gradio interface.")
        if MAX_TABS > 0:
            current_outputs_state[0] = gr.update(label="Input Error", visible=True)
            current_outputs_state[1] = gr.update(value="No input received. Please enter product requirements.")
        # If MAX_TABS is 0, this error won't be visible. Assume MAX_TABS >= 1.
        yield *current_outputs_state, MERMAID_TRIGGER
        return

    try:
        cleaned_requirements = input_parser.parse(raw_requirements_text)
        # Optionally, display cleaned_requirements. For now, focusing on use case tabs.
        # If MAX_TABS > 0, could prepend to the first tab or have a dedicated "Input" tab.
        # For simplicity, we'll just log it if not directly displayed.
        logger.info(f"Cleaned requirements: {cleaned_requirements[:200]}...")
    except TypeError as e:
        logger.exception(f"Error processing input: {e}")
        if MAX_TABS > 0:
            current_outputs_state[0] = gr.update(label="Processing Error", visible=True)
            current_outputs_state[1] = gr.update(value=f"Error processing input: {e}")
        yield *current_outputs_state, MERMAID_TRIGGER
        return

    use_cases_response = use_case_generator.generate_use_cases(cleaned_requirements)

    if use_cases_response and use_cases_response.use_cases:
        initial_reply_message = ""
        if use_cases_response.reply:
            initial_reply_message = f"**Note from UseCaseGenerator:** {use_cases_response.reply}\n\n---\n"
            logger.info(f"Reply from UseCaseGenerator: {use_cases_response.reply}")

        for uc_index, uc in enumerate(use_cases_response.use_cases):
            if uc_index >= MAX_TABS:
                logger.warning(
                    f"Maximum number of tabs ({MAX_TABS}) reached. Use case '{uc.title}' will not get a new tab."
                )
                # Optionally, append a message to the last tab's markdown if MAX_TABS > 0
                if MAX_TABS > 0:
                    last_tab_md_idx = (MAX_TABS - 1) * 2 + 1
                    # To append, we'd need the current content, which is complex with update objects.
                    # Simplest is to log and stop adding to new tabs.
                    # Or, could add a gr.Markdown.update(value="...", append=True) if supported, but it's not.
                break  # Stop processing more use cases for new tabs

            tab_content_parts = []

            # Update Tab visibility and label
            # Tab component is at current_outputs_state[uc_index * 2]
            # Markdown component is at current_outputs_state[uc_index * 2 + 1]
            current_outputs_state[uc_index * 2] = gr.update(
                label=f"UC {uc_index + 1}: {uc.title[:30].strip().rstrip('...') + '...' if len(uc.title) > 30 else uc.title.strip()}",
                visible=True,
            )

            # 1. Use case description
            if uc_index == 0 and initial_reply_message:  # Prepend general reply to first use case
                tab_content_parts.append(initial_reply_message)

            tab_content_parts.append(f"## Use Case: {uc.title} (ID: {uc.id})\n")
            tab_content_parts.append(f"**Description:**\n{uc.description}\n")
            current_outputs_state[uc_index * 2 + 1] = gr.update(value="".join(tab_content_parts))
            yield *current_outputs_state, MERMAID_TRIGGER

            # 2. Generate and append flowchart
            logger.info(f"Generating flowchart for use case: '{uc.title}'")
            flowchart_response = flowchart_generator.generate_flowchart(uc.description)
            flowchart_mermaid_code_for_search = ""

            if flowchart_response and flowchart_response.flowchart_mermaid_code:
                flowchart_mermaid_code_for_search = flowchart_response.flowchart_mermaid_code
                logger.info(f"Flowchart Mermaid Code: {flowchart_mermaid_code_for_search}")
                tab_content_parts.append("\n### Flowchart\n")
                if flowchart_response.reply:
                    tab_content_parts.append(f"_{flowchart_response.reply}_\n")
                # Ensure mermaid code block is correctly formatted
                tab_content_parts.append(f"\n{flowchart_mermaid_code_for_search.strip()}\n")
            else:
                logger.warning(f"Could not generate flowchart for use case: {uc.title}")
                tab_content_parts.append(f"\n_Could not generate flowchart for {uc.title}._\n")
            current_outputs_state[uc_index * 2 + 1] = gr.update(value="".join(tab_content_parts))
            yield *current_outputs_state, MERMAID_TRIGGER

            # 3. Search for MCPs/APIs and append
            logger.info(f"Searching for MCPs/APIs for use case: '{uc.title}'")
            search_query = f"Use Case Title: {uc.title}\nUse Case Description: {uc.description}\nMermaid Flowchart:\n{flowchart_mermaid_code_for_search}"

            try:
                # Call the async search_manager.search using asyncio.run()
                found_mcps = asyncio.run(search_manager.search(search_query))
            except Exception as e:
                logger.exception(f"Error during MCP search for use case '{uc.title}': {e}")
                found_mcps = []
                tab_content_parts.append(f"\n_An error occurred while searching for MCPs for {uc.title}._\n")

            if found_mcps:
                tab_content_parts.append("\n### Found MCPs/APIs\n")
                for mcp_result in found_mcps:
                    tab_content_parts.append(f"- **Name:** {mcp_result.get('name', 'N/A')}\n")
                    url = mcp_result.get("url", "N/A")
                    tab_content_parts.append(f"  - **URL:** {url}\n")
                    desc = mcp_result.get("description", "")
                    desc_safe = desc.replace("\n", " ").replace("|", "\\|")  # Basic Markdown escaping
                    tab_content_parts.append(
                        f"  - **Description:** {desc_safe[:200]}{'...' if len(desc_safe) > 200 else ''}\n"
                    )
                    if mcp_result.get("corresponding_functions"):
                        tab_content_parts.append(f"  - **Functions:** {mcp_result['corresponding_functions']}\n")
                    if mcp_result.get("reasoning"):
                        tab_content_parts.append(f"  - **Reasoning:** {mcp_result['reasoning']}\n")
                    if mcp_result.get("stars") is not None:
                        tab_content_parts.append(f"  - **Stars:** {mcp_result['stars']}\n")
                tab_content_parts.append("\n")  # Extra newline after list of MCPs
            else:
                # Check if error message was already added for this search
                if not tab_content_parts[-1].strip().startswith("_An error occurred"):
                    tab_content_parts.append(f"\n_No MCPs/APIs found for {uc.title}._\n")

            current_outputs_state[uc_index * 2 + 1] = gr.update(value="".join(tab_content_parts))
            yield *current_outputs_state, MERMAID_TRIGGER
    else:
        logger.warning("No use cases were generated by UseCaseGenerator, or an error occurred.")
        if MAX_TABS > 0:
            current_outputs_state[0] = gr.update(label="Result", visible=True)
            current_outputs_state[1] = gr.update(value="No use cases were generated, or an error occurred.\n")
        yield *current_outputs_state, MERMAID_TRIGGER
        return

    logger.info("Gradio app processing complete.")
    # The final state is yielded implicitly when the generator finishes.


# --- Gradio Blocks UI ---
with gr.Blocks() as demo:
    gr.HTML(MERMAID_LOADER)
    mermaid_script_inject = gr.HTML()
    gr.Markdown("# MCP Requirement Analyzer")
    gr.Markdown(
        "Input product requirements to generate use cases, Mermaid flowcharts for each use case, and recommended MCPs/APIs."
    )
    with gr.Row():
        with gr.Column(scale=1):  # Input column
            requirements_input = gr.Textbox(
                lines=15,
                label="Enter Product Requirements",
                placeholder="Describe your product or feature requirements here...",
            )
            submit_btn = gr.Button("Analyze Requirements")
            examples = [
                [
                    "I want to build a mobile app that allows users to take photos of plants and get them identified. The app should also provide care instructions for the identified plant."
                ],
                [
                    "Develop a web platform for local artists to showcase and sell their artwork. Users should be able to browse art, view artist profiles, and make purchases. Artists need a dashboard to manage their listings and sales."
                ],
            ]
            gr.Examples(examples=examples, inputs=requirements_input)

        with gr.Column(scale=2):  # Output column with tabs
            tab_items = []
            md_outputs = []
            if MAX_TABS > 0:
                with gr.Tabs(elem_id="dynamic_tabs_container") as tabs_container:
                    for i in range(MAX_TABS):
                        with gr.Tab(label=f"UC {i + 1}", visible=False, elem_id=f"tab_uc_{i+1}") as tab_item:
                            md_output = gr.Markdown(elem_id=f"md_output_uc_{i+1}")
                            tab_items.append(tab_item)
                            md_outputs.append(md_output)
            else:  # Fallback if MAX_TABS is 0 (though it should be >= 1)
                gr.Markdown("Output will appear here. (MAX_TABS is 0, configure at least 1 tab for results)")

    # Prepare the list of all output components for the click handler
    # This list must match the structure expected by the yields in process_requirements_gradio
    all_outputs = []
    if MAX_TABS > 0:
        for i in range(MAX_TABS):
            all_outputs.append(tab_items[i])
            all_outputs.append(md_outputs[i])
    else:
        # If MAX_TABS is 0, the process_requirements_gradio function will have issues
        # as it's designed to yield updates for tab and markdown pairs.
        # For robustness, ensure MAX_TABS is at least 1 in practice.
        # If we absolutely had to handle MAX_TABS=0, process_requirements_gradio would need
        # a different yielding structure, and a single Markdown output might be used here.
        # Given MAX_TABS=10, this 'else' branch for all_outputs is not hit.
        pass

    if MAX_TABS > 0:  # Only set up click if there are tabs to output to
        submit_btn.click(
            process_requirements_gradio, inputs=requirements_input, outputs=all_outputs + [mermaid_script_inject]
        )
    else:
        # If no tabs, clicking the button should perhaps show an error or do nothing.
        # For now, it won't be wired if MAX_TABS = 0.
        pass


if __name__ == "__main__":
    # To run this app, save it as e.g. gradio_app.py and run: python gradio_app.py
    # It will typically launch on http://127.0.0.1:7860
    if MAX_TABS == 0:
        logger.warning("MAX_TABS is set to 0. The Gradio UI will not display tabbed results effectively.")
        logger.warning("Please set MAX_TABS to a value >= 1 in the script.")

    logger.info("Launching Gradio Blocks interface...")
    server_port = int(os.environ.get("PORT", 7860))  # Use PORT from env, default to 7860 if not set
    demo.launch(server_name="0.0.0.0", server_port=server_port, share=False)
