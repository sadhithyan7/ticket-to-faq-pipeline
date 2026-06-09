import argparse
import logging
from src import config
from src.ingest import init_db, load_tickets_from_csv, store_tickets
from src.cluster import cluster_tickets, top_themes, derive_theme_label
from src.draft import draft_faq_for_cluster
from src.write import write_draft

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run the Ticket -> FAQ Pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    args = parser.parse_args()

    logger.info("=== Starting Ticket -> FAQ Pipeline ===")
    
    # 1. Init DB
    init_db(config.DB_PATH)
    
    # 2. Load + Store Tickets
    tickets = load_tickets_from_csv(args.input)
    store_tickets(tickets, config.DB_PATH)
    
    # 3. Cluster
    clusters = cluster_tickets(config.DB_PATH, config.CLUSTER_METHOD, config.NUM_CLUSTERS)
    
    if not clusters:
        logger.warning("No clusters formed. Exiting.")
        return

    # 4. Pick top themes
    top_cluster_ids = top_themes(clusters, config.TOP_N_THEMES)
    
    # 5. Draft FAQ -> Write .md
    summary = []
    
    for cid in top_cluster_ids:
        cluster_tickets_list = clusters[cid]
        theme_label = derive_theme_label(cluster_tickets_list)
        
        logger.info(f"Processing Theme: '{theme_label}' (Cluster {cid}) with {len(cluster_tickets_list)} tickets")
        
        # Draft FAQ
        markdown = draft_faq_for_cluster(cluster_tickets_list, theme_label)
        
        # Write Draft
        file_path = write_draft(theme_label, markdown, config.DB_PATH, config.DRAFTS_DIR)
        summary.append({"theme": theme_label, "tickets": len(cluster_tickets_list), "file": file_path})
        
    # 6. Print summary table
    logger.info("=== Pipeline Completed ===")
    print("\nSUMMARY TABLE:")
    print(f"{'Theme':<30} | {'Tickets':<8} | {'File'}")
    print("-" * 70)
    for row in summary:
        print(f"{row['theme'][:28]:<30} | {row['tickets']:<8} | {row['file']}")

if __name__ == "__main__":
    main()
