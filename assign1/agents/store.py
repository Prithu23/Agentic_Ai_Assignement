"""ChromaDB access shared by the agents."""
import random

import chromadb

from ingest.ingest import DB_PATH

_client = chromadb.PersistentClient(path=DB_PATH)


def questions():
    return _client.get_or_create_collection("questions")


def feedback():
    return _client.get_or_create_collection("feedback")


def _where(company, role):
    return {"$and": [{"company": company}, {"role": role}]}


def options():
    metas = questions().get(include=["metadatas"])["metadatas"]
    out = {}
    for m in metas:
        out.setdefault(m["company"], set()).add(m["role"])
    return {c: sorted(r) for c, r in sorted(out.items())}


def pick_questions(company, role, n):
    """Company/role questions via metadata filter, ordered easy -> hard with a random mix."""
    res = questions().get(where=_where(company, role), include=["documents", "metadatas"])
    rows = [
        {"id": i, "question": d, **m}
        for i, d, m in zip(res["ids"], res["documents"], res["metadatas"])
    ]
    random.shuffle(rows)
    rows = rows[:n]
    order = {"Easy": 0, "Medium": 1, "Hard": 2}
    rows.sort(key=lambda r: order.get(r["difficulty"], 1))
    return rows


def similar_feedback(company, role, text, k=4):
    """Semantic search over past feedback for this company/role."""
    res = feedback().query(query_texts=[text], n_results=k, where=_where(company, role))
    return [
        {"text": d, "outcome": m["outcome"], "round": m["round"]}
        for d, m in zip(res["documents"][0], res["metadatas"][0])
    ]


def all_feedback(company, role):
    res = feedback().get(where=_where(company, role), include=["documents", "metadatas"])
    return [
        {"text": d, "outcome": m["outcome"], "round": m["round"]}
        for d, m in zip(res["documents"], res["metadatas"])
    ]
