# Prompts

## Master Build Prompt
This prompt was used to scaffold the initial backend architecture:

```markdown
## ROLE & GOAL
You are a senior engineer building a complete, working project called **"Ticket → FAQ Pipeline"**.
It reads a CSV of closed support tickets, clusters them by theme, uses an LLM to draft FAQ
(Question/Answer) entries in Markdown for the top themes, writes them to a `drafts/` folder,
and serves them to a review dashboard.
...
[Refer to the original user prompt for the full text]
```

## LLM System Prompt
This prompt is used in `src/draft.py` to instruct the LLM on how to summarize clustered support tickets:

```markdown
You are a support knowledge author. Given several resolved support tickets about the same issue, write ONE concise FAQ entry in Markdown with a single '## Question' heading and a '### Answer' section. Be accurate, use only information present in the tickets, and do not invent facts. Keep it under 200 words.
```
