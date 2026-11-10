from collections import defaultdict

from agents import llm, store

SYSTEM = (
    "You are the Report Agent. Write a focused 4-step improvement plan (numbered, one line each) for the "
    "student based on their weakest categories and the past feedback patterns for their target company. "
    "Be specific and motivating."
)


def build(session):
    answered = [r for r in session.results if r.get("scores")]
    by_cat = defaultdict(list)
    for r in answered:
        by_cat[r["category"]].append(r["scores"]["overall"])
    cats = {c: round(sum(v) / len(v), 1) for c, v in by_cat.items()}

    def avg(key):
        return round(sum(r["scores"][key] for r in answered) / len(answered), 1) if answered else 0

    averages = {k: avg(k) for k in ("correctness", "depth", "communication", "overall")}
    ranked = sorted(cats.items(), key=lambda kv: kv[1])
    strengths = [c for c, s in ranked[::-1] if s >= 6][:3]
    gaps = [c for c, s in ranked if s < 6][:3]

    past = store.all_feedback(session.company, session.role)
    rejected = [f["text"] for f in past if f["outcome"] == "Rejected"][:4]
    plan_text = llm.ask(
        SYSTEM,
        f"Company: {session.company}, role: {session.role}\nAverages: {averages}\nCategory scores: {cats}\n"
        f"Why past candidates were rejected:\n" + "\n".join(f"- {t}" for t in rejected),
        max_tokens=350,
    )
    if plan_text:
        plan = [line.lstrip("0123456789.-) ").strip() for line in plan_text.splitlines() if line.strip()]
    else:
        plan = [f"Revise {c} fundamentals and practise explaining them with an example." for c in gaps] or [
            "Keep practising mixed questions to stay sharp."
        ]
        plan.append("Answer out loud in a Situation-Action-Result structure.")
        plan.append(f"Re-run a {session.company} mock interview in a week and beat today's score.")

    return {
        "company": session.company,
        "role": session.role,
        "answered": len(answered),
        "skipped": len(session.results) - len(answered),
        "averages": averages,
        "categories": cats,
        "strengths": strengths,
        "gaps": gaps,
        "plan": plan[:6],
    }
