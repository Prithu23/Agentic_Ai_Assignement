import re

from agents import llm

SYSTEM = (
    "You are the Evaluator Agent of a mock-interview coach. Score the candidate's answer from 0 to 10 on "
    "correctness (against the expected points), depth (detail, examples, trade-offs) and communication "
    "(clarity, structure). Be fair and specific. Return JSON with keys: correctness, depth, communication "
    "(numbers), strengths (list of <=3 short strings), gaps (list of <=3 short strings naming missing "
    "expected points), summary (one encouraging sentence)."
)

STOP = {"that", "with", "this", "from", "have", "give", "gives", "about", "their", "which", "into", "than", "when"}


def _words(text):
    return {w for w in re.findall(r"[a-z0-9+#]+", text.lower()) if len(w) > 3 and w not in STOP}


def _heuristic(question, answer):
    """Offline fallback: keyword coverage of the expected points."""
    points = [p.strip() for p in question["expected_points"].split(";") if p.strip()]
    ans = _words(answer)
    covered, missed = [], []
    for p in points:
        pw = _words(p)
        hit = len(pw & ans) / max(len(pw), 1)
        (covered if hit >= 0.34 else missed).append(p)
    n = len(answer.split())
    sentences = len([s for s in re.split(r"[.!?\n]", answer) if s.strip()])
    correctness = round(10 * len(covered) / max(len(points), 1), 1)
    depth = round(min(10, n / 8 + (2 if "example" in answer.lower() or "for instance" in answer.lower() else 0)), 1)
    communication = round(min(10, 3 + sentences * 1.5 + (2 if n > 25 else 0)), 1)
    return {
        "correctness": correctness,
        "depth": depth,
        "communication": communication,
        "strengths": [f"You covered: {p}" for p in covered[:3]],
        "gaps": [f"Missing: {p}" for p in missed[:3]],
        "summary": "Nice effort!" if correctness >= 5 else "Good start, let's sharpen this one.",
    }


def _clamp(v):
    try:
        return max(0.0, min(10.0, float(v)))
    except (TypeError, ValueError):
        return 0.0


def evaluate(question, answer):
    data = llm.ask_json(
        SYSTEM,
        f"Question: {question['question']}\nExpected points: {question['expected_points']}\n"
        f"Difficulty: {question['difficulty']}\nCandidate answer: {answer}",
    )
    if not data or "correctness" not in data:
        data = _heuristic(question, answer)
    scores = {k: _clamp(data.get(k)) for k in ("correctness", "depth", "communication")}
    scores["overall"] = round(sum(scores.values()) / 3, 1)
    return {
        **scores,
        "strengths": [str(s) for s in data.get("strengths", [])][:3],
        "gaps": [str(s) for s in data.get("gaps", [])][:3],
        "summary": str(data.get("summary", "")),
    }
