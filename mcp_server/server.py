import sqlite3
import os
from mcp.server.fastmcp import FastMCP
from src import config
from src.ingest import init_db, load_tickets_from_csv, store_tickets
from src.cluster import cluster_tickets, derive_theme_label
from src.draft import draft_faq_for_cluster
from src.write import write_draft

# Create FastMCP server
mcp = FastMCP("ticket-faq")

def get_db_connection():
    if not os.path.exists(config.DB_PATH):
        init_db(config.DB_PATH)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool()
def cluster_tickets(csv_path: str) -> str:
    """Run ingest and cluster tickets, return a text summary."""
    try:
        init_db(config.DB_PATH)
        tickets = load_tickets_from_csv(csv_path)
        store_tickets(tickets, config.DB_PATH)
        
        clusters = cluster_tickets(config.DB_PATH, config.CLUSTER_METHOD, config.NUM_CLUSTERS)
        if not clusters:
            return "No clusters formed."
            
        summary = f"Clustered {len(tickets)} tickets into {len(clusters)} clusters.\n\n"
        for cid, t_list in clusters.items():
            theme = derive_theme_label(t_list)
            summary += f"Cluster {cid}: '{theme}' ({len(t_list)} tickets)\n"
            
        return summary
    except Exception as e:
        return f"Error clustering tickets: {e}"

@mcp.tool()
def draft_faq(cluster_id: int) -> str:
    """Drafts and returns the Markdown FAQ for one cluster ID."""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM tickets WHERE cluster_id = ?", (cluster_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return f"No tickets found for cluster ID {cluster_id}"
            
        tickets = [dict(r) for r in rows]
        theme = derive_theme_label(tickets)
        
        markdown = draft_faq_for_cluster(tickets, theme)
        file_path = write_draft(theme, markdown, config.DB_PATH, config.DRAFTS_DIR)
        
        return f"Drafted FAQ for theme '{theme}' and saved to {file_path}:\n\n{markdown}"
    except Exception as e:
        return f"Error drafting FAQ: {e}"

@mcp.tool()
def list_drafts() -> list:
    """Returns current drafts from the DB."""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT id, theme, status FROM drafts")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    # To test with MCP Inspector:
    # npx @modelcontextprotocol/inspector py -m mcp_server.server
    mcp.run()
