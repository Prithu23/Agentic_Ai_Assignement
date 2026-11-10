from agents import llm, store

SYSTEM = (
    "You are the Interviewer Agent of a friendly mock-interview coach. You speak as the interviewer "
    "of the given company. Write a 1-2 sentence natural lead-in before asking the given question. "
    "Do not change the question and do not reveal expected points."
)


def start(session):
    return store.pick_questions(session.company, session.role, session.num)


def ask_current(session):
    q = session.current
    n = session.index + 1
    lead = llm.ask(
        SYSTEM,
        f"Company: {session.company}\nRole: {session.role}\nRound: {q['round']}\n"
        f"Question {n} of {len(session.questions)}: {q['question']}",
        max_tokens=120,
    )
    if not lead:
        lead = f"Round: {q['round']}. Question {n} of {len(session.questions)}."
    return {
        "lead": lead,
        "question": q["question"],
        "meta": {"round": q["round"], "category": q["category"], "difficulty": q["difficulty"]},
    }


def hint(session):
    """A nudge from the expected points without giving everything away."""
    points = [p.strip() for p in session.current["expected_points"].split(";") if p.strip()]
    return "Think about: " + (points[0] if points else "structure your answer with an example.")
