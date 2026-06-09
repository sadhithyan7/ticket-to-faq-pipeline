import logging
from groq import Groq
from openai import OpenAI
from src import config

logger = logging.getLogger(__name__)

def generate(user_prompt: str, system_prompt: str = "") -> str:
    """
    Generate text using the configured LLM provider (Groq or OpenRouter).
    Retries once per provider. If provider is 'auto', tries Groq then falls back to OpenRouter.
    """
    provider = config.LLM_PROVIDER.lower()
    
    if provider == "groq":
        return _call_groq(user_prompt, system_prompt)
    elif provider == "openrouter":
        return _call_openrouter(user_prompt, system_prompt)
    else: # auto
        try:
            return _call_groq(user_prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Groq generation failed: {e}. Falling back to OpenRouter.")
            return _call_openrouter(user_prompt, system_prompt)

def _call_groq(user_prompt: str, system_prompt: str) -> str:
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set or empty.")
    
    client = Groq(api_key=config.GROQ_API_KEY, max_retries=1)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages
    )
    logger.info(f"Served by Groq, model: {config.GROQ_MODEL}")
    return response.choices[0].message.content

def _call_openrouter(user_prompt: str, system_prompt: str) -> str:
    if not config.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set or empty.")
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.OPENROUTER_API_KEY,
        max_retries=1
    )
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    
    response = client.chat.completions.create(
        model=config.OPENROUTER_MODEL,
        messages=messages
    )
    logger.info(f"Served by OpenRouter, model: {config.OPENROUTER_MODEL}")
    return response.choices[0].message.content
