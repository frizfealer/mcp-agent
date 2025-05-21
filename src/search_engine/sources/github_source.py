"""Source handler for searching GitHub."""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dotenv import load_dotenv
from github import Auth, Github
from markdown_it import MarkdownIt
from openai import OpenAI
from pydantic import BaseModel

from src.config import get_llm_api_key
from src.search_engine.sources.base_source import BaseSourceHandler

GITHUB_CACHE_PATHS = {
    "modelcontextprotocol/servers": "resources/github/modelcontextprotocol_servers.md",
    "punkpeye/awesome-mcp-servers": "resources/github/punkpeye_awesome_mcp_servers.md",
    "appcypher/awesome-mcp-servers": "resources/github/appcypher_awesome-mcp-servers.md",
}


logger = logging.getLogger(__name__)
MODEL_NAME = "gpt-4.1-mini"

SYSTEM_PROMPT = """
Analyze a given use case and three curated lists of Model Context Protocols (MCPs) to determine the most appropriate MCPs for the user's use case. 
Provide expert advice and recommendations based on your findings.

# Steps

1. **Understand the Use Case**: Carefully read and comprehend the user's specific use case requirements.
2. **Come up with a list of functionalities needed for the use case.
3. **Review MCP Lists**: Examine the two provided lists of MCPs sourced from GitHub readme.md files to identify potential matches.
4. **Matching Process**: 
   - Compare the functionalities from 2) and features of MCPs with the requirements of the use case.
   - Consider the compatibility, reliability, and community support of the MCPs.
5. **Advice and Recommendation**:
   - Provide a well-reasoned recommendation for the MCPs that best fit the use case.
   - Include reasoning for each recommendation. 
   - Provide a list of functions that the MCPs can provide to the use case.
   - Recommend 3 - 6 MCPs best suited for the use case.

# Notes

- Ensure to consider compatibility, reliability, and community support during the matching process.
- Discuss any alternatives or additional considerations if needed, but focus on providing clear and directed recommendations.

# Curated MCP List 1 (modelcontextprotocol/servers)

{curated_file1}

# Curated MCP list 2 (punkpeye/awesome-mcp-servers)

{curated_file2}

# Curated MCP list 3 (appcypher/awesome-mcp-servers)

{curated_file3}
"""


class MCPCandidate(BaseModel):
    """
    Represents a single search result for an MCP (Model Context Protocol).
    """

    name: str
    description: str
    url: str
    corresponding_functions: List[str]
    reasoning: str
    stars: Optional[int] = None


class MCPCandidates(BaseModel):
    """
    Represents the expected JSON structure from the LLM, containing a list of MCP candidates.
    """

    MCP_candidates: List[MCPCandidate]


class GitHubSource(BaseSourceHandler):
    """
    Handles searching for Model Context Protocols (MCPs) on GitHub.
    """

    def __init__(
        self,
    ):
        super().__init__(source_name="GitHub")
        self.client = OpenAI(api_key=get_llm_api_key())
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            logger.info("GITHUB_TOKEN is not set, using prefetched repositories as searching sources.")
            self.github_client = None
        else:
            self.github_client = Github(auth=Auth.Token(github_token))
            logger.info("PyGithub client initialized successfully.")

    def _is_file_older_than_a_week(self, file_path):
        """We have the cached readme files by default, so we don't need to check if the file exists."""
        file_mtime = os.path.getmtime(file_path)
        file_datetime = datetime.fromtimestamp(file_mtime)
        return datetime.now() - file_datetime > timedelta(weeks=1)

    def _update_github_cache_if_needed(self) -> Dict[str, str]:
        curated_files = {}
        if self.github_client is None:
            logger.info("No GitHub client available, skipping cache update.")
            for repo, file_path in GITHUB_CACHE_PATHS.items():
                with open(file_path, "r") as file:
                    curated_files[repo] = file.read()
            return curated_files

        for repo, file_path in GITHUB_CACHE_PATHS.items():
            if self._is_file_older_than_a_week(file_path):
                logger.info(f"Updating cache for {repo} (file: {file_path})...")
                try:
                    repo_obj = self.github_client.get_repo(repo)
                    readme_content = repo_obj.get_readme().decoded_content.decode("utf-8")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(readme_content)
                    logger.info(f"Updated {file_path} from {repo}.")
                    curated_files[repo] = readme_content
                except Exception as e:
                    logger.exception(f"Failed to update {file_path} from {repo}: {e}")
            else:
                logger.info(f"Cache for {repo} is up to date.")
                with open(file_path, "r") as file:
                    curated_files[repo] = file.read()
        return curated_files

    def _extract_section_with_keyword(self, md_text, keyword):
        md = MarkdownIt()
        tokens = md.parse(md_text)
        result = []
        in_section = False
        current_level = None
        for token in tokens:
            if token.type == "heading_open":
                heading_level = int(token.tag[1])  # e.g., 'h2' → 2
                heading_text = tokens[tokens.index(token) + 1].content.lower()

                if keyword.lower() in heading_text:
                    in_section = True
                    current_level = heading_level
                    continue

                if in_section and heading_level <= current_level:
                    # Stop collecting at next heading of same or higher level
                    break
            if in_section:
                result.append(token.content if hasattr(token, "content") else "")
        return "\n".join(result).strip()

    def post_processing(
        self,
        mcp_candidates: List[MCPCandidate],
    ):
        if self.github_client is not None:
            for mcp_candidate in mcp_candidates:
                github_repo_id = "/".join(mcp_candidate.url.split("https://github.com/")[1].split("/")[:2])
                try:
                    repo_obj = self.github_client.get_repo(github_repo_id)
                    stars = repo_obj.stargazers_count
                    mcp_candidate.stars = stars
                except Exception as e:
                    logger.exception(f"Failed to get stars for {github_repo_id}: {e}")
        return mcp_candidates

    async def search(self, use_case_description: str):
        """
        Searches GitHub for relevant repositories or code.
        """
        curated_files = self._update_github_cache_if_needed()
        curated_file1 = self._extract_section_with_keyword(curated_files["modelcontextprotocol/servers"], "servers")
        curated_file2 = self._extract_section_with_keyword(
            curated_files["punkpeye/awesome-mcp-servers"], "Server Implementations"
        )
        curated_file3 = curated_files["appcypher/awesome-mcp-servers"]
        system_prompt = SYSTEM_PROMPT.format(
            curated_file1=curated_file1,
            curated_file2=curated_file2,
            curated_file3=curated_file3,
        )

        user_prompt = f"Use case description: {use_case_description}"
        logger.info("Searching over curated lists of MCPs/APIs...")
        response = self.client.responses.parse(
            model=MODEL_NAME,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=MCPCandidates,
        )
        MCP_candidates = [i for i in response.output_parsed.MCP_candidates if i.url != ""]
        MCP_candidates = self.post_processing(MCP_candidates)
        return [i.model_dump() for i in MCP_candidates]


if __name__ == "__main__":
    import asyncio

    load_dotenv(override=True)

    async def main():
        use_case_description = (
            "I need a Model Context Protocol (MCP) that supports real-time collaborative editing, robust access control, "
            "and integration with external data sources. Please recommend the best MCPs for this use case."
        )
        github_source = GitHubSource()
        try:
            results = await github_source.search(use_case_description)
            print("Search Results:")
            for candidate in results:
                for k, v in candidate.items():
                    print(f"{k}: {v}")
                print("\n")
        except Exception as e:
            print(f"Error during search: {e}")

    asyncio.run(main())
