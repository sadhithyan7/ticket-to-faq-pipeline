import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
CLUSTER_METHOD: str = os.getenv("CLUSTER_METHOD", "embeddings")
NUM_CLUSTERS: int = int(os.getenv("NUM_CLUSTERS", "6"))
TOP_N_THEMES: int = int(os.getenv("TOP_N_THEMES", "5"))
DB_PATH: str = os.getenv("DB_PATH", "tickets.sqlite")
DRAFTS_DIR: str = os.getenv("DRAFTS_DIR", "drafts")
