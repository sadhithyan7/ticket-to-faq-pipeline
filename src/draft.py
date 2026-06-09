import logging
from src import llm
from typing import List, Dict

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a support knowledge author. Given several resolved support tickets about the same issue, write ONE concise FAQ entry in Markdown with a single '## Question' heading and a '### Answer' section. Be accurate, use only information present in the tickets, and do not invent facts. Keep it under 200 words."""

def draft_faq_for_cluster(cluster_tickets: List[Dict], theme: str) -> str:
    """
    Build a prompt from tickets, call LLM, and return the Markdown string.
    """
    logger.info(f"Drafting FAQ for theme: '{theme}' with {len(cluster_tickets)} tickets.")
    
    # Build user prompt
    user_prompt_lines = [f"Theme: {theme}\n", "Tickets:"]
    for i, t in enumerate(cluster_tickets, 1):
        user_prompt_lines.append(f"\n--- Ticket {i} ---")
        user_prompt_lines.append(f"Subject: {t['subject']}")
        user_prompt_lines.append(f"Description: {t['description']}")
        user_prompt_lines.append(f"Resolution: {t['resolution']}")
        
    user_prompt = "\n".join(user_prompt_lines)
    
    # Call LLM
    try:
        markdown_output = llm.generate(user_prompt=user_prompt, system_prompt=SYSTEM_PROMPT)
        return markdown_output
    except Exception as e:
        logger.error(f"Failed to draft FAQ for theme '{theme}': {e}")
        return f"## Question\nFailed to generate FAQ for {theme}.\n\n### Answer\nError: {e}"
