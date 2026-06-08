"""
BM25-based RAG retriever for the Kynto security knowledge base.

Indexes both security_sft.jsonl (Q&A pairs) and combined_sft.jsonl so the
SecurityAnalystAgent can pull the most relevant context before calling the model.

No GPU required — BM25 runs entirely on CPU.
"""

import json
import re
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# BM25 (pure-Python fallback if rank_bm25 not installed)
# ---------------------------------------------------------------------------
try:
    from rank_bm25 import BM25Okapi as _BM25Impl
    _USE_RANK_BM25 = True
except ImportError:
    _USE_RANK_BM25 = False


def _tokenize(text: str) -> List[str]:
    """Lowercase + split on non-alphanumeric chars."""
    return re.findall(r"[a-z0-9]+", text.lower())


class _SimpleBM25:
    """Minimal BM25-Okapi when rank_bm25 isn't available."""

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        import math
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.N = len(corpus)
        self.avgdl = sum(len(d) for d in corpus) / max(1, self.N)

        # term frequency per doc
        self.tf: List[dict] = []
        for doc in corpus:
            freq: dict = {}
            for t in doc:
                freq[t] = freq.get(t, 0) + 1
            self.tf.append(freq)

        # document frequency
        df: dict = {}
        for freq in self.tf:
            for t in freq:
                df[t] = df.get(t, 0) + 1

        self.idf: dict = {}
        for t, n in df.items():
            self.idf[t] = math.log((self.N - n + 0.5) / (n + 0.5) + 1)

    def get_scores(self, query: List[str]) -> List[float]:
        scores = [0.0] * self.N
        for t in query:
            idf = self.idf.get(t, 0.0)
            for i, freq in enumerate(self.tf):
                f = freq.get(t, 0)
                dl = len(self.corpus[i])
                denom = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i] += idf * (f * (self.k1 + 1)) / denom
        return scores


# ---------------------------------------------------------------------------
# Document record
# ---------------------------------------------------------------------------
class Document:
    def __init__(self, question: str, answer: str, source: str):
        self.question = question
        self.answer   = answer
        self.source   = source
        # Combined text used for indexing
        self.text = f"{question} {answer}"

    def __repr__(self) -> str:
        return f"Document(q={self.question[:60]!r})"


# ---------------------------------------------------------------------------
# RAG retriever
# ---------------------------------------------------------------------------
class SecurityRAG:
    """
    Index the Kynto security corpus and retrieve the top-k most relevant
    documents for any query using BM25.

    Usage::

        rag = SecurityRAG()
        context = rag.format_context("What is SQL injection?")
        # → "Relevant knowledge:\\n- SQL injection (CWE-89)..."
    """

    def __init__(
        self,
        data_paths: Optional[List[str]] = None,
        top_k: int = 3,
    ):
        self.top_k = top_k
        self.docs: List[Document] = []

        if data_paths is None:
            data_paths = [
                "data_sft/security_sft.jsonl",
                "data_sft/combined_sft.jsonl",
            ]

        for path in data_paths:
            self._load_jsonl(path)

        self._build_index()
        print(
            f"[RAG] indexed {len(self.docs)} documents "
            f"({'rank_bm25' if _USE_RANK_BM25 else 'built-in BM25'})",
            flush=True,
        )

    # ------------------------------------------------------------------
    def _load_jsonl(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            print(f"[RAG] warning: {path} not found, skipping", flush=True)
            return

        seen: set = set()
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj  = json.loads(line)
                    msgs = obj["messages"]
                    q    = msgs[0]["content"].strip()
                    a    = msgs[1]["content"].strip()
                    key  = (q[:80], a[:80])
                    if key in seen:
                        continue
                    seen.add(key)
                    self.docs.append(Document(q, a, source=p.name))
                except Exception:
                    continue

    # ------------------------------------------------------------------
    def _build_index(self) -> None:
        tokenized = [_tokenize(d.text) for d in self.docs]
        if _USE_RANK_BM25:
            self._bm25 = _BM25Impl(tokenized)
        else:
            self._bm25 = _SimpleBM25(tokenized)

    # ------------------------------------------------------------------
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Document]:
        """Return top-k documents most relevant to query."""
        if not self.docs:
            return []

        k      = top_k or self.top_k
        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)

        ranked = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )

        return [self.docs[i] for i in ranked[:k] if scores[i] > 0.0]

    # ------------------------------------------------------------------
    def format_context(self, query: str, top_k: Optional[int] = None) -> str:
        """Return a formatted context string ready to inject into a prompt."""
        results = self.retrieve(query, top_k)
        if not results:
            return ""

        lines = ["[Relevant security knowledge]"]
        for i, doc in enumerate(results, 1):
            # Truncate long answers to keep context manageable
            answer = doc.answer[:400].rstrip()
            if len(doc.answer) > 400:
                answer += "..."
            lines.append(f"{i}. Q: {doc.question}\n   A: {answer}")

        return "\n\n".join(lines)
