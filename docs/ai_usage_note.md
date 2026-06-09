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
- Environment should be set beforehand with all previuos installation packages.
- API calling error while conencting and testing pipelines
- 
