from src import config
from src import llm

print(f"Loaded Provider: {config.LLM_PROVIDER}")
print(f"Groq API Key length: {len(config.GROQ_API_KEY)}")

try:
    response = llm.generate("Say hello in 3 words")
    print(f"Response: {response}")
except Exception as e:
    print(f"Generation skipped or failed: {e}")
