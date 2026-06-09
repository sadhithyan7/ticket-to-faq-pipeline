import sqlite3
import logging
from typing import Dict, List, Tuple
from collections import defaultdict

# We import ML libraries dynamically inside functions or with try/except 
# so we only load what we need based on the method
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

def cluster_tickets(db_path: str, method: str, num_clusters: int) -> Dict[int, List[Dict]]:
    """
    Cluster tickets using either 'embeddings' or 'tfidf'.
    Writes cluster_id back to DB and returns grouped tickets.
    """
    logger.info(f"Clustering with method={method}, num_clusters={num_clusters}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, subject, description, resolution FROM tickets")
    rows = cursor.fetchall()
    
    if not rows:
        logger.warning("No tickets to cluster.")
        return {}
        
    tickets = [dict(r) for r in rows]
    texts = [f"{t['subject']} {t['description']}" for t in tickets]
    
    if method == "embeddings":
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(texts)
            X = embeddings
        except ImportError:
            logger.error("sentence-transformers is not installed. Falling back to tfidf.")
            method = "tfidf"
            
    if method == "tfidf":
        from sklearn.feature_extraction.text import TfidfVectorizer
        logger.info("Using TfidfVectorizer...")
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        X = vectorizer.fit_transform(texts)
        
    logger.info(f"Running KMeans with k={num_clusters}...")
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(X)
    
    clusters = defaultdict(list)
    for i, ticket in enumerate(tickets):
        cluster_id = int(labels[i])
        ticket['cluster_id'] = cluster_id
        clusters[cluster_id].append(ticket)
        
        # Write back to DB
        cursor.execute("UPDATE tickets SET cluster_id = ? WHERE id = ?", (cluster_id, ticket['id']))
        
    conn.commit()
    conn.close()
    
    logger.info("Clustering completed and saved to DB.")
    return dict(clusters)

def top_themes(clusters: Dict[int, List[Dict]], top_n: int) -> List[int]:
    """Pick the largest clusters."""
    cluster_sizes = [(cid, len(tickets)) for cid, tickets in clusters.items()]
    cluster_sizes.sort(key=lambda x: x[1], reverse=True)
    top_cluster_ids = [cid for cid, size in cluster_sizes[:top_n]]
    logger.info(f"Top {top_n} themes identified: {top_cluster_ids}")
    return top_cluster_ids

def derive_theme_label(tickets: List[Dict]) -> str:
    """Derive a short human theme label from a cluster of tickets using TF-IDF."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    texts = [f"{t['subject']} {t['description']}" for t in tickets]
    
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=3)
        vectorizer.fit(texts)
        keywords = vectorizer.get_feature_names_out()
        return " ".join(keywords).title()
    except Exception as e:
        # Fallback if too few words etc
        logger.warning(f"Could not derive theme label: {e}")
        return "General Issue"
