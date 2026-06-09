# AI Usage Note

## What AI helped with
The AI (Google Antigravity) was instrumental in rapidly scaffolding and implementing the entire backend pipeline. It correctly generated:
- The SQLite database initialization and ingestion logic using Pandas.
- The clustering module using SentenceTransformers and KMeans, along with a fallback TF-IDF vectorizer.
- The LLM integration, setting up both Groq and OpenRouter (OpenAI SDK) as primary and fallback providers.
- The FastAPI server for UI integration and the FastMCP server for tool exposition.
- The comprehensive test suite and prompt design.

## What it got wrong
- There were minor inconsistencies between how the configuration variables were exported from `src/config.py` (initially as lower-case fields on a dataclass instance) and how they were imported in the rest of the application (as upper-case module-level constants). This required a quick refactoring to align the module variables.
- The FastMCP tool function names had the `run_` prefix which didn't strictly align with the user prompt's specification.

## Best 3 prompts
1. **Master Prompt**: The overarching master prompt effectively laid out the entire project architecture in a single shot, providing strict constraints, exact technology stack versions, and precise folder structures.
2. **Implementation Plan Approval**: Requesting verification of the auto-generated boilerplate, prompting the agent to cross-check each phase methodically.
3. **The System Prompt**: "You are a support knowledge author. Given several resolved support tickets about the same issue, write ONE concise FAQ entry in Markdown with a single '## Question' heading and a '### Answer' section. Be accurate, use only information present in the tickets, and do not invent facts. Keep it under 200 words."
