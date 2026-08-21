from .providers import generate_with_fallback


def generate_answer(question: str, chunks: list[str], sources: list[str], history: list[dict] = None) -> dict:
    """Generate a grounded answer with citations. Uses Groq → Ollama fallback."""
    context_parts = []
    for i, (chunk, source) in enumerate(zip(chunks, sources)):
        context_parts.append(f"[Source {i + 1}: {source}]\n{chunk}")

    context = "\n\n---\n\n".join(context_parts)

    system_prompt = """You are a research assistant that answers questions strictly from the provided source material.

RULES:
1. Answer ONLY using information from the provided source chunks.
2. Cite the source URL for every claim using [Source N] format.
3. If the provided chunks do not contain enough information to answer the question, say "The provided sources do not contain enough information to answer this question." — do NOT use your general knowledge.
4. Be precise and concise.
5. If sources conflict, note the discrepancy and cite both."""

    user_message = f"""Source material:
{context}

---

Question: {question}"""

    answer, provider = generate_with_fallback(system_prompt, user_message, history=history)

    # Extract citations from answer and map them to actual chunks
    citations = []
    seen = set()
    for i, (chunk, source) in enumerate(zip(chunks, sources)):
        marker = f"[Source {i + 1}]"
        if marker in answer and source not in seen:
            snippet = chunk.strip()
            if len(snippet) > 250:
                snippet = snippet[:247] + "..."
            citations.append({"url": source, "snippet": snippet})
            seen.add(source)

    # Clean up the answer text (remove [Source N] and boilerplate prefixes)
    import re
    # Remove markers like [Source 1], [Source 1, 2], [Source 1][Source 2]
    answer_clean = re.sub(r"\[Source\s*\d+([,\s]*\d+)*\]", "", answer)
    # Strip duplicate spaces and newlines around them
    answer_clean = re.sub(r"\s+", " ", answer_clean).strip()

    # Remove boilerplate prefixes
    prefixes = [
        r"^based\s+on\s+the\s+(provided\s+)?(source|text|document|wikipedia|excerpt)s?\s*(material|excerpts|information|chunks)?(,\s*)?",
        r"^according\s+to\s+the\s+(provided\s+)?(source|text|document|wikipedia|excerpt)s?\s*(material|excerpts|information|chunks)?(,\s*)?"
    ]
    for pref in prefixes:
        answer_clean = re.sub(pref, "", answer_clean, flags=re.IGNORECASE)

    answer_clean = answer_clean.strip()
    if answer_clean and answer_clean[0].islower():
        answer_clean = answer_clean[0].upper() + answer_clean[1:]

    return {
        "answer": answer_clean,
        "citations": citations,
        "found_in_sources": len(citations) > 0,
        "provider": provider,
    }
