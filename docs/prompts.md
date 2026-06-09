# Prompts

## Master Build Prompt
# MASTER BUILD PROMPT — Ticket → FAQ Pipeline
---
## ROLE & GOAL
You are a senior engineer building a complete, working project called **"Ticket → FAQ Pipeline"**.
It reads a CSV of closed support tickets, clusters them by theme, uses an LLM to draft FAQ
(Question/Answer) entries in Markdown for the top themes, writes them to a `drafts/` folder,
and serves them to a review dashboard.

Build the ENTIRE backend end-to-end. The frontend React UI will be provided separately
(generated in v0.dev) — your job for the frontend is only to set up the `frontend/` folder
and make the backend connect to it cleanly (CORS + a stable API contract).

This project MUST demonstrate all three of these (a hackathon requirement):
1. **Agent loop** — `run.py` runs the full pipeline autonomously, step by step.
2. **MCP tool (built)** — an MCP server exposing the pipeline as callable tools.
3. **External API integration** — calling a free LLM API (Groq, with OpenRouter as backup).

## HARD CONSTRAINTS
- Runtime dependencies must be **free / open-source**. No paid services baked into the app.
- The LLM is called via a **free API key** the user provides (Groq primary, OpenRouter backup).
- Never hardcode model names or keys — read them from environment variables.
- Never commit secrets. Provide `.env.example`, and ensure `.env` is gitignored.
- If you are unsure of a library's exact API, use its simplest documented usage and add a
  short comment saying so. Do NOT invent functions, parameters, or model names.
- Keep functions small, type-hinted, and logged. Prefer the standard library where possible.

## TECH STACK (use exactly these)
- Language: **Python 3.11+**
- Web API: **FastAPI** + **Uvicorn**
- Data: **pandas** for CSV, **sqlite3** (Python stdlib) for storage
- Clustering: **sentence-transformers** (`all-MiniLM-L6-v2`) + **scikit-learn** `KMeans`,
  with a lightweight **TF-IDF + KMeans** fallback (scikit-learn only, no model download)
- LLM: **groq** SDK (primary) and **openai** SDK pointed at OpenRouter (backup)
- MCP: official **mcp** Python SDK (`mcp.server.fastmcp.FastMCP`). If that import path is
  unavailable, use the **fastmcp** package instead — do not guess a third option.
- Tests: **pytest**
- Config: **python-dotenv**

## FOLDER STRUCTURE (create exactly this)
```
ticket-to-faq-pipeline/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config.py        # loads env vars
│   ├── llm.py           # unified LLM client with Groq->OpenRouter fallback
│   ├── ingest.py        # CSV -> SQLite
│   ├── cluster.py       # embeddings/TF-IDF + KMeans, pick top N
│   ├── draft.py         # build prompt from a cluster, call LLM, return markdown
│   ├── write.py         # save draft .md to drafts/, update DB status
│   ├── run.py           # THE AGENT LOOP: orchestrates the whole pipeline (CLI)
│   └── api.py           # FastAPI app + CORS + endpoints
├── mcp_server/
│   └── server.py        # FastMCP server exposing pipeline tools
├── frontend/            # v0.dev React app goes here (leave a placeholder README)
├── sample_data/
│   ├── tickets.csv      # ~50 fake tickets across ~6 themes
│   └── expected_drafts/ # generated drafts committed as expected output
├── drafts/              # runtime output (.md files)
├── tests/
│   └── test_pipeline.py
└── docs/
    ├── ai_usage_note.md
    └── prompts.md
```

## ENVIRONMENT (.env.example — create this file)
```
# LLM provider selection: groq | openrouter | auto  (auto = try groq, then openrouter)
LLM_PROVIDER=auto

# Groq (primary) — get a free key at console.groq.com
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# OpenRouter (backup) — get a free key at openrouter.ai ; ":free" models cost nothing
OPENROUTER_API_KEY=
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct

# Pipeline settings
CLUSTER_METHOD=embeddings        # embeddings | tfidf
NUM_CLUSTERS=6                   # KMeans k
TOP_N_THEMES=5                   # how many top clusters to draft FAQs for
DB_PATH=tickets.sqlite
DRAFTS_DIR=drafts
```
NOTE: model IDs above are sensible defaults; they are configurable via env. If a model id is
rejected at runtime, surface the error clearly so the user can swap the env value.

## requirements.txt (create this)
```
fastapi
uvicorn[standard]
pandas
scikit-learn
sentence-transformers
groq
openai
mcp
python-dotenv
pytest
httpx
```

## MODULE SPECS

### src/config.py
- Load `.env` with python-dotenv. Expose typed settings (provider, keys, model names,
  cluster method, num_clusters, top_n, db_path, drafts_dir) as a simple config object/dict.

### src/llm.py  (the external-API integration with fallback)
- One public function: `generate(user_prompt: str, system_prompt: str = "") -> str`.
- Behavior based on `LLM_PROVIDER`:
  - `groq`: use the `groq` SDK — `Groq(api_key=GROQ_API_KEY).chat.completions.create(model=GROQ_MODEL, messages=[...])`.
  - `openrouter`: use the `openai` SDK with `base_url="https://openrouter.ai/api/v1"` and `OPENROUTER_API_KEY`, model `OPENROUTER_MODEL`.
  - `auto`: try Groq first; on any exception OR missing/empty Groq key, fall back to OpenRouter.
- Add one retry per provider. Log which provider/model actually served the request.
- Return the assistant message text as a plain string.

### src/ingest.py
- `init_db(db_path)`: create tables `tickets(id, subject, description, resolution, cluster_id)`
  and `drafts(id, theme, markdown, status)` where status ∈ {draft, approved}.
- `load_tickets_from_csv(csv_path) -> list[dict]`: read with pandas; expected columns
  `subject, description, resolution`. Validate columns; raise a clear error if missing.
- `store_tickets(rows, db_path)`: insert into `tickets`.

### src/cluster.py
- `cluster_tickets(db_path, method, num_clusters) -> dict[int, list[ticket]]`:
  - If `method == "embeddings"`: encode `subject + " " + description` with
    SentenceTransformer('all-MiniLM-L6-v2'); run sklearn KMeans(n_clusters=num_clusters).
  - If `method == "tfidf"`: TfidfVectorizer -> KMeans. (No model download — use this if torch is unavailable.)
  - Write each ticket's `cluster_id` back to the DB. Return clusters grouped by id.
- `top_themes(clusters, top_n) -> list[cluster_id]`: pick the largest clusters.
- For each top cluster, derive a short human theme label (e.g. most common keywords).

### src/draft.py
- `draft_faq_for_cluster(cluster_tickets: list[dict], theme: str) -> str`:
  - Build a prompt summarizing the tickets and their resolutions.
  - Use this SYSTEM prompt:
    "You are a support knowledge author. Given several resolved support tickets about the
     same issue, write ONE concise FAQ entry in Markdown with a single '## Question' heading
     and a '### Answer' section. Be accurate, use only information present in the tickets,
     and do not invent facts. Keep it under 200 words."
  - Call `llm.generate(...)` and return the Markdown string.

### src/write.py
- `write_draft(theme, markdown, db_path, drafts_dir) -> path`: write `drafts/<slug>.md`,
  insert a row into `drafts` with status='draft'. Slugify the theme for the filename.

### src/run.py  (THE AGENT LOOP — this is the headline feature)
- CLI: `python -m src.run --input sample_data/tickets.csv`
- Steps, logged clearly as it goes:
  1. init_db  2. load + store tickets  3. cluster  4. pick top themes
  5. for each top theme: draft FAQ -> write .md  6. print a summary table of what was created.
- This single command must take a CSV and produce reviewable drafts with no manual steps.

### src/api.py  (so the v0.dev dashboard can connect)
- FastAPI app. Add CORS middleware allowing `http://localhost:3000` and `http://localhost:5173`.
- Endpoints (THIS IS THE FRONTEND CONTRACT — do not change shapes):
  - `GET  /api/health` -> {status:"ok"}
  - `POST /api/run` -> runs the pipeline on sample_data/tickets.csv (or an uploaded path); returns a summary.
  - `GET  /api/drafts` -> list of {id, theme, status, markdown}
  - `GET  /api/drafts/{id}` -> single draft object
  - `PUT  /api/drafts/{id}` body {markdown} -> updates the draft text
  - `POST /api/drafts/{id}/approve` -> sets status="approved"
- Read/write via the SQLite DB.

### mcp_server/server.py  (the MCP capability)
- Use `from mcp.server.fastmcp import FastMCP`. Create `mcp = FastMCP("ticket-faq")`.
- Expose three `@mcp.tool()` functions that reuse the src/ modules:
  - `cluster_tickets(csv_path: str) -> str` — runs ingest+cluster, returns a text summary.
  - `draft_faq(cluster_id: int) -> str` — drafts and returns the Markdown for one cluster.
  - `list_drafts() -> list` — returns current drafts from the DB.
- Run over stdio: `if __name__ == "__main__": mcp.run()`.
- Add a short comment on how to test it with the MCP Inspector.

## SAMPLE DATA (generate this)
- Create `sample_data/tickets.csv` with ~50 rows, columns `subject,description,resolution`,
  spread across ~6 realistic themes (e.g. login/password, billing, app crash, slow performance,
  feature request, account deletion). Vary the wording so clustering is meaningful.
- After the pipeline runs, copy the produced drafts into `sample_data/expected_drafts/`.

## TESTS (tests/test_pipeline.py)
- Happy path with a tiny in-test CSV (use a temp dir / temp DB):
  ingest -> cluster returns the expected number of groups -> a draft `.md` is written.
- Mock or stub the LLM call so tests don't need a network/key.
- `pytest -q` must pass.

## DOCS
- `docs/prompts.md`: paste the key prompts used (this build prompt + the LLM system prompt).
- `docs/ai_usage_note.md`: a 1-page note — what AI helped with, what it got wrong, best 3 prompts.

## BUILD WORKFLOW (do in this order; after each phase, RUN the check before continuing)
1. Scaffold folders + files + requirements.txt + .env.example + .gitignore. `pip install -r requirements.txt`.
2. config.py + llm.py. Check: a tiny script calls `generate("Say hello in 3 words")` and prints the provider used.
3. ingest.py + DB. Check: load sample CSV, confirm row count in SQLite.
4. cluster.py. Check: cluster the sample data, print cluster sizes.
5. draft.py + write.py. Check: draft one cluster, confirm a .md file appears in drafts/.
6. run.py agent loop. Check: one command produces all top-N drafts.
7. api.py + CORS. Check: `uvicorn src.api:app --reload`, hit /api/health and /api/drafts.
8. mcp_server/server.py. Check: server starts; tools are listed.
9. tests. Check: `pytest -q` passes.
10. docs + sample_data/expected_drafts. Final check: fresh clone, follow README, it runs.

## GUARDRAILS (anti-hallucination)
- Make reasonable assumptions and note them in comments instead of stopping to ask.
- Never fabricate library APIs or model names; if uncertain, use documented basics + a comment.
- Keep the API response shapes exactly as specified so the v0.dev frontend connects unchanged.
- All secrets via env only; verify `.env` is in `.gitignore` before any commit.

## Efficieny improving prompt for faq generation
In my Ticket → FAQ Pipeline project, the FAQ generation 
step is too slow. Fix it by reducing the number of FAQs 
generated.

Current behavior:
- KMeans clusters into 5 groups
- Generates 1 FAQ per cluster = 5 FAQ files every run

Change it to:

═══════════════════════════════════════
CHANGE 1 — src/clusterer.py
═══════════════════════════════════════
Reduce KMeans clusters from 5 to 3.
Only return the TOP 3 clusters ranked by ticket count
(largest clusters first = most important topics).

═══════════════════════════════════════
CHANGE 2 — src/faq_generator.py  
═══════════════════════════════════════
- Only process clusters with MORE than 3 tickets
  (skip small/irrelevant clusters)
- Reduce max_tokens in the Groq API call from 1000 to 400
- Use this faster, shorter prompt to the LLM:
  "Write a short FAQ entry (max 3 lines for the answer).
   Q: (one clear question)
   A: (max 3 bullet points only)
   Based on these tickets: {ticket summaries}"

═══════════════════════════════════════
CHANGE 3 — src/main.py
═══════════════════════════════════════
Add a config variable at the top:

  MAX_FAQS = 3  ← easy to change later

Pass MAX_FAQS into the pipeline so only that many 
FAQ files are ever generated per run.

═══════════════════════════════════════
RULES
═══════════════════════════════════════
- Do not change any other files
- Keep all existing error handling
- Print: "Generating X of Y FAQs..." so user sees progress
- Output the 3 changed files completely

## LLM System Prompt
This prompt is used in `src/draft.py` to instruct the LLM on how to summarize clustered support tickets:

```markdown
You are a support knowledge author. Given several resolved support tickets about the same issue, write ONE concise FAQ entry in Markdown with a single '## Question' heading and a '### Answer' section. Be accurate, use only information present in the tickets, and do not invent facts. Keep it under 200 words.
```
