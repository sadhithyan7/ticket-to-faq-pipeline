from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from typing import List, Dict, Any
from src import config

app = FastAPI(title="Ticket -> FAQ Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    if not os.path.exists(config.DB_PATH):
        from src.ingest import init_db
        init_db(config.DB_PATH)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/health")
def health():
    return {"status": "ok"}
    
@app.post("/api/run")
async def run_pipeline(file: UploadFile = File(None)):
    from dotenv import load_dotenv
    from src.ingest import init_db, load_tickets_from_csv, store_tickets
    from src.cluster import cluster_tickets, top_themes, derive_theme_label
    from src.draft import draft_faq_for_cluster
    from src.write import write_draft
    import shutil, importlib

    # Force-reload .env so new API keys are picked up without restart
    load_dotenv(override=True)
    importlib.reload(config)
    
    csv_path = "sample_data/tickets.csv"
    if file:
        os.makedirs("uploads", exist_ok=True)
        csv_path = os.path.join("uploads", "active_tickets.csv")
        with open(csv_path, "wb") as f:
            f.write(await file.read())
            
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail=f"CSV file not found at {csv_path}")
        
    try:
        # Clear old data completely before each fresh run
        if os.path.exists(config.DB_PATH):
            os.remove(config.DB_PATH)
        if os.path.exists(config.DRAFTS_DIR):
            shutil.rmtree(config.DRAFTS_DIR)
        os.makedirs(config.DRAFTS_DIR, exist_ok=True)

        init_db(config.DB_PATH)
        try:
            tickets = load_tickets_from_csv(csv_path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
        store_tickets(tickets, config.DB_PATH)
        
        # Dynamically scale clusters and themes based on the dataset size
        num_tickets = len(tickets)
        dynamic_num_clusters = max(config.NUM_CLUSTERS, num_tickets // 4)
        dynamic_top_n = min(20, max(config.TOP_N_THEMES, dynamic_num_clusters))
        
        clusters = cluster_tickets(config.DB_PATH, config.CLUSTER_METHOD, dynamic_num_clusters)
        if not clusters:
            return {"status": "no clusters formed"}
            
        top_cluster_ids = top_themes(clusters, dynamic_top_n)
        
        summary = []
        for cid in top_cluster_ids:
            cluster_tickets_list = clusters[cid]
            theme_label = derive_theme_label(cluster_tickets_list)
            markdown = draft_faq_for_cluster(cluster_tickets_list, theme_label)
            file_path = write_draft(theme_label, markdown, config.DB_PATH, config.DRAFTS_DIR)
            summary.append({"theme": theme_label, "tickets": len(cluster_tickets_list), "file": file_path})
            
        return {"status": "completed", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drafts")
def get_drafts():
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM drafts")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return []

@app.get("/api/drafts/{draft_id}")
def get_draft(draft_id: int):
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    raise HTTPException(status_code=404, detail="Draft not found")

@app.put("/api/drafts/{draft_id}")
def update_draft(draft_id: int, markdown: str = Body(..., embed=True)):
    conn = get_db_connection()
    cursor = conn.execute("UPDATE drafts SET markdown = ? WHERE id = ?", (markdown, draft_id))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "updated"}

@app.post("/api/drafts/{draft_id}/approve")
def approve_draft(draft_id: int):
    conn = get_db_connection()
    cursor = conn.execute("UPDATE drafts SET status = 'approved' WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "approved"}

# Mount the frontend directory to serve the static HTML dashboard
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

