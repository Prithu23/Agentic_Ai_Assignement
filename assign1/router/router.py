import re

from agents import llm

INTENTS = ("practice", "evaluate", "coach", "hint", "skip", "report")

SYSTEM = (
    "Classify the student's message in a mock-interview app into exactly one intent: "
    "practice (answering the current question or asking for the next one), "
    "evaluate (asking how their answer scored or why), "
    "coach (asking for advice or what the company looks for), "
    "hint, skip, or report (finish and see summary). "
    'Return JSON: {"intent": "..."}'
)

RULES = [
    ("report", r"\b(finish|end (the )?(interview|session)|report|summary|i'?m done)\b"),
    ("skip", r"^\s*(skip|pass|next question|i don'?t know)\b"),
    ("hint", r"\b(hint|clue|stuck|help me start)\b"),
    ("evaluate", r"\b(score|evaluate|rate|how did i do|why .*score|marks|grade)\b"),
    ("coach", r"\b(coach|advice|tips?|improve|what (do|does) .* (look|want|expect)|how (can|do) i|feedback|prepare)\b"),
]


def route(message, awaiting_answer):
    text = message.strip().lower()
    for intent, pattern in RULES:
        if re.search(pattern, text):
            # a long, detailed message that happens to contain a keyword is probably an answer
            if awaiting_answer and len(text.split()) > 40 and intent in ("coach", "evaluate"):
                break
            return intent
    if awaiting_answer and len(text.split()) >= 6:
        return "practice"
    data = llm.ask_json(SYSTEM, f"Awaiting an answer: {awaiting_answer}\nMessage: {message}", max_tokens=40)
    if data and data.get("intent") in INTENTS:
        return data["intent"]
    return "practice" if awaiting_answer else "coach"
