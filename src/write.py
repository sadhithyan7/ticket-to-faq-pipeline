import sqlite3
import os
import re
import logging

logger = logging.getLogger(__name__)

def slugify(text: str) -> str:
    """Convert text to a safe filename slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    if not text:
        text = "draft"
    return text

def write_draft(theme: str, markdown: str, db_path: str, drafts_dir: str) -> str:
    """
    Write markdown to drafts/<slug>.md and insert a row into the drafts table.
    """
    os.makedirs(drafts_dir, exist_ok=True)
    slug = slugify(theme)
    file_path = os.path.join(drafts_dir, f"{slug}.md")
    
    # Write file
    logger.info(f"Writing draft to {file_path}")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)
        
    # Insert into DB
    logger.info(f"Inserting draft '{theme}' into database")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO drafts (theme, markdown, status)
        VALUES (?, ?, 'draft')
    ''', (theme, markdown))
    conn.commit()
    conn.close()
    
    return file_path
