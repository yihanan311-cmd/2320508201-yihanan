import json
import os


class SessionMemory:
    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get_history(self, max_turns: int = 10) -> list:
        return self.messages[-(max_turns * 2):]

    def clear(self):
        self.messages = []


class PersistentMemory:
    def __init__(self, path: str):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        return {"topics_studied": [], "notes": [], "quiz_scores": []}

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_topic(self, topic: str):
        if topic not in self.data["topics_studied"]:
            self.data["topics_studied"].append(topic)
            self.save()

    def add_note(self, content: str):
        self.data["notes"].append(content)
        self.save()

    def add_quiz_score(self, score: float):
        self.data["quiz_scores"].append(score)
        self.save()

    def get_summary(self) -> str:
        topics = "、".join(self.data["topics_studied"]) or "无"
        notes_count = len(self.data["notes"])
        scores = self.data["quiz_scores"]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        return f"已学主题：{topics}；笔记{notes_count}条；平均测验得分：{avg}"
