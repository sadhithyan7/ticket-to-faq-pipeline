# Ticket → FAQ Pipeline

This project processes support tickets, clusters them by theme, and uses an LLM to generate draft FAQs for top themes.

## Team Details

- **Team Name**: Techies
- **Team Members**:
  - [Adhithyan S]
  - [Hariharan K]
  - [Abirami B] 
  - [Kalpana L] 


## Architecture Overview

1. **Ingestion**: Reads CSV data using Pandas and stores it in SQLite.
2. **Clustering**: Groups tickets into common themes using Sentence-Transformers & KMeans (with TF-IDF fallback).
3. **Drafting**: Builds a context prompt for the LLM to generate an FAQ entry.
4. **Writing**: Saves the markdown draft and updates the DB.
5. **API & MCP**: Exposes functionality via a FastAPI web server and a FastMCP server.

## Setup Instructions

1. Clone the repository: `git clone [repository_url]`
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your API keys (Groq or OpenRouter).

## Run Instructions

To run the full agent loop end-to-end:
```bash
python -m src.run --input sample_data/tickets.csv
```

To run the API server:
```bash
uvicorn src.api:app --reload
```



- The clustering algorithm requires a reasonable number of tickets to form meaningful groups.
- The default setup relies on `groq` or `openrouter` free-tier API endpoints. Rate limits may apply.
