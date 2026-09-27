"""Quiz engine for Telegram bot - 12 domains *10 Q"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random
from .domains import DOMAINS
from .quiz import QUIZZES, get_quiz

@dataclass
class QuizSession:
    chat_id: int
    domain_id: str
    questions: List = field(default_factory=list)
    current: int = 0
    score: int = 0
    answered: List[Dict] = field(default_factory=list)

class QuizManager:
    def __init__(self):
        self.sessions: Dict[int, QuizSession] = {}

    def start(self, chat_id: int, domain_id: Optional[str]=None) -> QuizSession:
        # if no domain, pick random domain weighted by importance (high risk first)
        if not domain_id:
            # prioritize high-risk domains
            high = [d.id for d in DOMAINS if d.risk_level=="high"]
            domain_id = random.choice(high)
        qs = get_quiz(domain_id)
        if not qs:
            # fallback random 10 from all
            qs = random.sample(QUIZZES, 10)
        # shuffle but keep 10
        qs_shuffled = random.sample(qs, min(10, len(qs)))
        sess = QuizSession(chat_id=chat_id, domain_id=domain_id, questions=qs_shuffled, current=0, score=0)
        self.sessions[chat_id] = sess
        return sess

    def current_question(self, chat_id: int):
        sess = self.sessions.get(chat_id)
        if not sess or sess.current >= len(sess.questions):
            return None
        return sess.questions[sess.current]

    def answer(self, chat_id: int, choice_idx: int) -> Dict:
        sess = self.sessions.get(chat_id)
        if not sess:
            return {"error": "no session"}
        q = sess.questions[sess.current]
        is_correct = (choice_idx == q.correct_index)
        if is_correct:
            sess.score += 1
        sess.answered.append({
            "q_id": q.q_id,
            "choice": choice_idx,
            "correct": q.correct_index,
            "is_correct": is_correct
        })
        sess.current += 1
        finished = sess.current >= len(sess.questions)
        result = {
            "is_correct": is_correct,
            "correct_index": q.correct_index,
            "correct_text": q.options_fa[q.correct_index],
            "explanation": q.explanation_fa,
            "score": sess.score,
            "total": len(sess.questions),
            "finished": finished,
            "domain_id": sess.domain_id
        }
        if finished:
            # keep for stats but remove session after? Keep for final report
            pass
        return result

    def get_domain_title(self, domain_id: str) -> str:
        for d in DOMAINS:
            if d.id==domain_id:
                return d.title_fa
        return domain_id

    def format_question(self, q) -> str:
        opts = "\n".join([f"{i+1}) {opt}" for i, opt in enumerate(q.options_fa)])
        return f"❓ {q.question_fa}\n\n{opts}\n\nبا عدد 1-4 جواب بده (مثلا 2)"

    def format_result(self, chat_id: int) -> str:
        sess = self.sessions.get(chat_id)
        if not sess:
            return "آزمونی فعال نیست. /azmoon بزن"
        pct = sess.score*100//len(sess.questions) if sess.questions else 0
        badge = "🏆 عالی! مدرک آگاه به حقوق" if pct>=70 else "📚 بیشتر بخون"
        return f"پایان آزمون {self.get_domain_title(sess.domain_id)}\n\nامتیاز: {sess.score}/{len(sess.questions)} ({pct}%)\n{badge}\n\nبرای آزمون جدید: /azmoon\nبرای دانش: /danesh {sess.domain_id}\nبرای شغل: /shoghle"

# Global singleton
quiz_manager = QuizManager()
