from .providers import generate_with_fallback


def generate_answer(question: str, chunks: list[str], sources: list[str]) -> dict:
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

    answer, provider = generate_with_fallback(system_prompt, user_message)

    # Extract citations from answer
    citations = []
    seen = set()
    for i, source in enumerate(sources):
        marker = f"[Source {i + 1}]"
        if marker in answer and source not in seen:
            idx = answer.find(marker)
            start = max(0, idx - 100)
            end = min(len(answer), idx + 100)
            snippet = answer[start:end].strip()
            citations.append({"url": source, "snippet": snippet})
            seen.add(source)

    return {
        "answer": answer,
        "citations": citations,
        "found_in_sources": True,
        "provider": provider,
    }
