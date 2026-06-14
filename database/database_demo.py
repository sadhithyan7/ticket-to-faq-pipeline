
import sqlite3
import os

DB_PATH = "tickets.sqlite"

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database file '{DB_PATH}' does not exist yet. Please run the pipeline from the UI first to create and populate it.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("1. DATABASE TABLES")
    print("=" * 60)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f" - Table Name: {table[0]}")

    print("\n" + "=" * 60)
    print("2. SCHEMAS (PRAGMA table_info)")
    print("=" * 60)
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"{'ID':<4} | {'Column Name':<20} | {'Type':<12} | {'Not Null':<8} | {'PK':<4}")
        print("-" * 60)
        for col in columns:
            # col: (cid, name, type, notnull, dflt_value, pk)
            print(f"{col[0]:<4} | {col[1]:<20} | {col[2]:<12} | {col[3]:<8} | {col[5]:<4}")

    print("\n" + "=" * 60)
    print("3. DATA COUNTS & SAMPLES")
    print("=" * 60)
    
    # Tickets sample
    cursor.execute("SELECT COUNT(*) FROM tickets;")
    ticket_count = cursor.fetchone()[0]
    print(f"Total Tickets: {ticket_count}")
    
    if ticket_count > 0:
        print("\nSample Ticket Row:")
        cursor.execute("SELECT id, subject, cluster_id FROM tickets LIMIT 1;")
        row = cursor.fetchone()
        print(f"  - ID: {row[0]}")
        print(f"  - Subject: '{row[1]}'")
        print(f"  - Cluster ID: {row[2]}")
        
    # Drafts sample
    cursor.execute("SELECT COUNT(*) FROM drafts;")
    draft_count = cursor.fetchone()[0]
    print(f"Total FAQ Drafts: {draft_count}")
    
    if draft_count > 0:
        print("\nSample Draft FAQ Row:")
        cursor.execute("SELECT id, theme, status FROM drafts LIMIT 1;")
        row = cursor.fetchone()
        print(f"  - ID: {row[0]}")
        print(f"  - Theme: '{row[1]}'")
        print(f"  - Status: '{row[2]}'")

    conn.close()

if __name__ == "__main__":
    main()
