import json
import os
import re
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _ollama_up():
    try:
        urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=1)
        return True
    except Exception:
        return False


def provider():
    forced = os.getenv("LLM_PROVIDER", "").lower()
    if forced == "gemini":
        return "gemini" if os.getenv("GOOGLE_API_KEY") else None
    if forced == "ollama":
        return "ollama" if _ollama_up() else None
    if forced == "anthropic" or os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic" if os.getenv("ANTHROPIC_API_KEY") else None
    return "ollama" if _ollama_up() else None



def available():
    return provider() is not None

def _model(max_tokens):
    p = provider()
    if p == "gemini":
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, max_output_tokens=max_tokens)
    if p == "ollama":
        return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_URL, num_predict=max_tokens)
    return ChatAnthropic(model=MODEL, max_tokens=max_tokens)


def _extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0)) if match else None


def build_chain(system, max_tokens=700, as_json=False):
    """LCEL chain: prompt template | chat model | output parser."""
    prompt = ChatPromptTemplate.from_messages([("system", "{system}"), ("human", "{input}")])
    model = _model(max_tokens)
    parser = StrOutputParser()
    if as_json:
        return prompt | model | parser | RunnableLambda(_extract_json)
    return prompt | model | parser


def ask(system, user, max_tokens=700):
    """Return the model's text, or None if no key is set or the call fails."""
    if not available():
        return None
    try:
        return build_chain(system, max_tokens).invoke({"system": system, "input": user}).strip()
    except Exception as e:
        print("LLM error:", e)
        return None


def ask_json(system, user, max_tokens=700):
    if not available():
        return None
    system += "\nRespond with a single JSON object and nothing else."
    try:
        return build_chain(system, max_tokens, as_json=True).invoke({"system": system, "input": user})
    except Exception as e:
        print("LLM error:", e)
        return None
