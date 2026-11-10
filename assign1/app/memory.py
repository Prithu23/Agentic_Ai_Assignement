import uuid
from dataclasses import dataclass, field


@dataclass
class Session:
    company: str
    role: str
    questions: list
    num: int = 5
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    index: int = 0
    awaiting_answer: bool = True
    results: list = field(default_factory=list)  # one dict per answered/skipped question
    history: list = field(default_factory=list)  # [{"who": "user"|"buddy", "text": str}]

    @property
    def current(self):
        return self.questions[self.index] if self.index < len(self.questions) else None

    @property
    def finished(self):
        return self.index >= len(self.questions)

    def remember(self, who, text):
        self.history.append({"who": who, "text": text})
        self.history = self.history[-20:]


SESSIONS = {}


def create(company, role, num):
    s = Session(company=company, role=role, questions=[], num=num)
    SESSIONS[s.id] = s
    return s


def get(session_id):
    return SESSIONS.get(session_id)
