import os
import math
import re
from collections import Counter


class KnowledgeBase:
    def __init__(self):
        self.docs = {}  # filename -> full text
        self.chunks = []  # list of (source, chunk_text)
        self.tfidf = []  # list of {term: tfidf_score} per chunk

    def load(self, directory: str):
        for fname in os.listdir(directory):
            if fname.endswith(".txt"):
                path = os.path.join(directory, fname)
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                self.docs[fname] = text
                for chunk in self._split(text):
                    self.chunks.append((fname, chunk))
        self._build_tfidf()

    def _split(self, text: str, size: int = 200) -> list:
        sentences = re.split(r"[。\n]", text)
        chunks, buf = [], ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(buf) + len(s) > size and buf:
                chunks.append(buf)
                buf = s
            else:
                buf += s + "。"
        if buf:
            chunks.append(buf)
        return chunks

    def _tokenize(self, text: str) -> list:
        return list(text)  # character-level for Chinese

    def _build_tfidf(self):
        N = len(self.chunks)
        df = Counter()
        tfs = []
        for _, chunk in self.chunks:
            tokens = self._tokenize(chunk)
            tf = Counter(tokens)
            tfs.append(tf)
            for t in set(tokens):
                df[t] += 1
        self.tfidf = []
        for tf in tfs:
            total = sum(tf.values())
            scores = {}
            for t, cnt in tf.items():
                scores[t] = (cnt / total) * math.log((N + 1) / (df[t] + 1))
            self.tfidf.append(scores)

    def search(self, query: str, top_k: int = 3) -> list:
        if not self.chunks:
            return []
        q_tokens = self._tokenize(query)
        scores = []
        for i, vec in enumerate(self.tfidf):
            score = sum(vec.get(t, 0) for t in q_tokens)
            scores.append((score, i))
        scores.sort(reverse=True)
        results = []
        for score, i in scores[:top_k]:
            source, chunk = self.chunks[i]
            results.append({"source": source, "content": chunk, "score": round(score, 4)})
        return results
