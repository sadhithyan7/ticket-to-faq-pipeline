import sqlite3
import pandas as pd
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def init_db(db_path: str):
    """Initialize the SQLite database with tickets and drafts tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            resolution TEXT NOT NULL,
            cluster_id INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme TEXT NOT NULL,
            markdown TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {db_path}")

def load_tickets_from_csv(csv_path: str) -> List[Dict]:
    """Read tickets from a CSV using pandas and validate columns."""
    logger.info(f"Loading tickets from {csv_path}")
    df = pd.read_csv(csv_path)
    
    required_cols = {'subject', 'description', 'resolution'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"CSV is missing required columns: {missing}")
        
    # Handle NaN values to prevent issues
    df = df.fillna("")
    
    return df.to_dict('records')

def store_tickets(rows: List[Dict], db_path: str):
    """Insert ticket records into the tickets table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted = 0
    for row in rows:
        cursor.execute("""
            INSERT INTO tickets (subject, description, resolution)
            VALUES (?, ?, ?)
        """, (row.get('subject', ''), row.get('description', ''), row.get('resolution', '')))
        inserted += 1
        
    conn.commit()
    conn.close()
    logger.info(f"Stored {inserted} tickets into {db_path}")
