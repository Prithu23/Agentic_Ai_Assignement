from agents import llm, store

SYSTEM = (
    "You are the Coach Agent of a mock-interview coach, talking directly to a student in a warm, upbeat tone. "
    "Ground every tip in the PAST FEEDBACK snippets provided (real feedback given to earlier candidates of this "
    "company and role). Mention the pattern, e.g. 'candidates who ...'. Give 3 concrete, short bullet tips. "
    "Never invent feedback that is not in the snippets."
)


def _format(items):
    return "\n".join(f"- [{f['round']} / {f['outcome']}] {f['text']}" for f in items)


def coach(session, focus=None, evaluation=None):
    """Coaching grounded in retrieved historical feedback. Returns (text, sources)."""
    query = focus or (session.current["question"] if session.current else f"{session.company} interview")
    if evaluation and evaluation["gaps"]:
        query += " " + " ".join(evaluation["gaps"])
    items = store.similar_feedback(session.company, session.role, query)

    context = f"Company: {session.company}\nRole: {session.role}\n"
    if evaluation:
        context += f"Latest answer scores: {evaluation}\n"
    context += f"Student asked: {focus or 'general advice'}\nPAST FEEDBACK:\n{_format(items)}"

    text = llm.ask(SYSTEM, context, max_tokens=450)
    if not text:
        text = "Here's what past candidates were told:\n" + "\n".join(f"• {f['text']}" for f in items[:3])
    return text, items
