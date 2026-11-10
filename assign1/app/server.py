import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402

from agents import coach, evaluator, interviewer, llm, report, store  # noqa: E402
from app import memory  # noqa: E402
from router.router import route  # noqa: E402

app = Flask(__name__, static_folder=str(ROOT / "web"), static_url_path="")


def msg(agent, text, kind="text"):
    return {"agent": agent, "text": text, "kind": kind}


def progress(s):
    return {"index": min(s.index, len(s.questions)), "total": len(s.questions)}


@app.get("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/options")
def options():
    return jsonify({"options": store.options(), "llm": llm.available(), "provider": llm.provider()})


@app.post("/api/start")
def start():
    d = request.get_json(force=True)
    s = memory.create(d["company"], d["role"], int(d.get("num", 5)))
    s.questions = interviewer.start(s)
    if not s.questions:
        return jsonify({"error": "No questions found for that company and role."}), 404
    return jsonify({"session_id": s.id, "next": interviewer.ask_current(s), "progress": progress(s)})


def finish(s, out):
    s.awaiting_answer = False
    out["report"] = report.build(s)
    out["messages"].append(msg("Report", "That's a wrap! Here's your session report.", "report"))


def advance(s, out):
    s.index += 1
    if s.finished:
        finish(s, out)
    else:
        out["next"] = interviewer.ask_current(s)
        s.awaiting_answer = True


@app.post("/api/chat")
def chat():
    d = request.get_json(force=True)
    s = memory.get(d.get("session_id"))
    if not s:
        return jsonify({"error": "Unknown session. Start a new interview."}), 404
    text = d["message"].strip()
    s.remember("user", text)

    intent = route(text, s.awaiting_answer and not s.finished)
    out = {"intent": intent, "messages": [], "next": None, "report": None}

    if s.finished and intent in ("practice", "skip", "hint"):
        intent = out["intent"] = "report"

    if intent == "practice":
        q = s.current
        ev = evaluator.evaluate(q, text)
        s.results.append({"qid": q["id"], "category": q["category"], "answer": text, "scores": ev})
        out["scores"] = ev
        out["messages"].append(msg("Evaluator", ev["summary"], "scores"))
        tip, sources = coach.coach(s, evaluation=ev)
        out["messages"].append(msg("Coach", tip, "coach"))
        out["sources"] = sources
        advance(s, out)
    elif intent == "skip":
        q = s.current
        s.results.append({"qid": q["id"], "category": q["category"], "answer": None, "scores": None})
        out["messages"].append(msg("Interviewer", "No worries, skipping that one. Ideal answers cover: " + q["expected_points"]))
        advance(s, out)
    elif intent == "hint":
        out["messages"].append(msg("Interviewer", interviewer.hint(s)))
    elif intent == "evaluate":
        last = next((r for r in reversed(s.results) if r["scores"]), None)
        if last:
            out["scores"] = last["scores"]
            out["messages"].append(msg("Evaluator", "Here's how your last answer scored.", "scores"))
        else:
            out["messages"].append(msg("Evaluator", "Answer a question first and I'll score it!"))
    elif intent == "coach":
        tip, sources = coach.coach(s, focus=text)
        out["messages"].append(msg("Coach", tip, "coach"))
        out["sources"] = sources
    elif intent == "report":
        finish(s, out)

    out["progress"] = progress(s)
    out["awaiting_answer"] = s.awaiting_answer
    for m in out["messages"]:
        s.remember("buddy", m["text"])
    return jsonify(out)


if __name__ == "__main__":
    app.run(debug=False, port=5000)
