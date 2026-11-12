# Interview Buddy: Company-Smart Mock Interview Coach

Run everything from this folder:

```
pip install -r requirements.txt
copy .env.example .env        # then put your ANTHROPIC_API_KEY in .env (optional)
python ingest/ingest.py       # loads the CSVs into ChromaDB (once)
python app/server.py          # open http://localhost:5000
```

Without an API key the app runs in offline mode (keyword-based scoring, retrieved feedback shown as-is).

| Part | File |
|---|---|
| Interviewer agent (RAG over questions) | `agents/interviewer.py`, `agents/store.py` |
| Evaluator agent | `agents/evaluator.py` |
| Coach agent (RAG over past feedback) | `agents/coach.py` |
| Report agent | `agents/report.py` |
| Intent router | `router/router.py` |
| Conversation memory | `app/memory.py` |
| API + static server | `app/server.py` |
| Front end | `web/index.html`, `web/style.css`, `web/app.js` |
