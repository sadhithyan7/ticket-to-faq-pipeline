import os
import sqlite3
import pytest
from src.ingest import init_db, load_tickets_from_csv, store_tickets
from src.cluster import cluster_tickets
from src.draft import draft_faq_for_cluster
from src.write import write_draft
import pandas as pd

# Mock LLM generation
import src.llm as mock_llm
mock_llm.generate = lambda user_prompt, system_prompt="": "## Question\nMocked Question?\n\n### Answer\nMocked Answer."

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    init_db(str(db_path))
    return str(db_path)

@pytest.fixture
def temp_csv(tmp_path):
    csv_path = tmp_path / "tickets.csv"
    data = {
        "subject": ["Login issue", "Cannot login", "Billing problem", "Invoice request"],
        "description": ["I forgot my password", "Reset password link not working", "Charge is wrong", "Need my last invoice"],
        "resolution": ["Sent reset link", "Fixed link", "Refunded", "Emailed invoice"]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def drafts_dir(tmp_path):
    return str(tmp_path / "drafts")

def test_pipeline_happy_path(temp_db, temp_csv, drafts_dir):
    # 1. Ingest
    tickets = load_tickets_from_csv(temp_csv)
    assert len(tickets) == 4
    store_tickets(tickets, temp_db)
    
    # Verify in DB
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM tickets")
    assert cursor.fetchone()[0] == 4
    
    # 2. Cluster (use tfidf for tests to avoid downloading models)
    clusters = cluster_tickets(temp_db, method="tfidf", num_clusters=2)
    assert len(clusters) <= 2
    
    # 3. Draft & Write
    cid = list(clusters.keys())[0]
    theme = "Test Theme"
    markdown = draft_faq_for_cluster(clusters[cid], theme)
    assert "Mocked Question" in markdown
    
    file_path = write_draft(theme, markdown, temp_db, drafts_dir)
    assert os.path.exists(file_path)
    
    # Verify draft in DB
    cursor.execute("SELECT * FROM drafts")
    draft_row = cursor.fetchone()
    assert draft_row is not None
    conn.close()
