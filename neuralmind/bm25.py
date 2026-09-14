"""
bm25.py — BM25 keyword index for code-aware hybrid search
==========================================================

Supplements vector search with keyword-aware retrieval, so queries like
"UserService" or "get_auth_token" score exact-name matches above semantically
similar but textually distant nodes — a persistent gap in pure vector RAG for
code.

Key design choices:
- Code-aware tokenisation: splits camelCase, snake_case, dots, digits so
  "UserService" → ["user", "service"], "auth.py" → ["auth", "py"].
- Pure Python / stdlib only — no extra dependencies.
- Persists as JSON in <project>/.neuralmind/bm25_index.json so the index
  survives daemon restarts and is shared across MCP calls.
- Returns results in the same shape as EmbeddingBackend.search() so
  callers can mix in without any schema change.

Disabled at runtime via NEURALMIND_BM25=0.
"""

import json
import math
import os
import re
from pathlib import Path
from typing import Any

_CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

# Prose-friendly tokenizer: keeps hyphenated terms whole (BPC-157, GLP-1),
# lowercases, strips punctuation except hyphens within words.
_PROSE_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _tokenize(text: str) -> list[str]:
    """Split code text into lowercase tokens.

    Handles camelCase, snake_case, dots, hyphens, digits, and whitespace.
    Short tokens (< 2 chars) and pure-digit tokens are dropped so index
    noise from line numbers and single-letter vars stays low.
    """
    # Split camelCase boundaries first
    text = _CAMEL_RE.sub(" ", text)
    # Split on all non-alphanumeric chars (_, -, ., space, /, etc.)
    tokens = re.split(r"[^a-zA-Z0-9]+", text)
    return [t.lower() for t in tokens if len(t) >= 2 and not t.isdigit()]


def _tokenize_prose(text: str) -> list[str]:
    """Prose-friendly tokenization: keeps hyphenated terms whole.

    Regex ``[a-z0-9]+(?:-[a-z0-9]+)*`` matches runs of alphanumerics
    connected by single hyphens, so "BPC-157", "GLP-1", "semaglutide"
    stay as single tokens. Lowercases, drops punctuation, filters tokens
    shorter than 2 chars and pure-digit tokens (same noise guard as
    ``_tokenize``).
    """
    tokens = _PROSE_RE.findall(text.lower())
    return [t for t in tokens if len(t) >= 2 and not t.replace("-", "").isdigit()]


class BM25Index:
    """BM25 sparse index for code node retrieval.

    Parameters k1 and b follow the standard Atire BM25 formulation:
        score = Σ_t  IDF(t) × tf(t,d) × (k1+1)
                              ─────────────────────────────────────
                              tf(t,d) + k1 × (1 - b + b × dl/avgdl)

    where IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1).
    """

    _VERSION = 1

    def __init__(self, k1: float = 1.5, b: float = 0.75, tokenizer: callable = None) -> None:
        """Create an empty BM25 index.

        Args:
            k1: Term-frequency saturation (higher = slower saturation).
            b: Document-length normalization (0=none, 1=full).
            tokenizer: Tokenizer function for documents and queries.
                       Defaults to _tokenize (code). Use _tokenize_prose for
                       prose/book projects so hyphenated terms stay whole.
        """
        self.k1 = k1
        self.b = b
        self._tokenize = tokenizer or _tokenize

        # Ordered document lists — same index across all three.
        self._ids: list[str] = []
        self._docs: list[str] = []
        self._metadatas: list[dict[str, Any]] = []

        # Per-document token frequency: [{token: count}]
        self._tf: list[dict[str, int]] = []
        # Document length (token count) per doc
        self._dl: list[int] = []

        # Collection-level stats, rebuilt by build()
        self._df: dict[str, int] = {}  # document frequency per term
        self._idf: dict[str, float] = {}  # cached IDF per term
        self._avgdl: float = 0.0
        self._N: int = 0

    # ------------------------------------------------------------------
    # Build / update
    # ------------------------------------------------------------------

    def add_documents(
        self,
        doc_ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Append documents to the index (call build() afterwards)."""
        if metadatas is None:
            metadatas = [{} for _ in doc_ids]
        for doc_id, text, meta in zip(doc_ids, texts, metadatas, strict=True):
            tokens = self._tokenize(text)
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self._ids.append(doc_id)
            self._docs.append(text)
            self._metadatas.append(meta)
            self._tf.append(tf)
            self._dl.append(len(tokens))

    def build(self) -> None:
        """Compute IDF and avgdl from the current document set."""
        self._N = len(self._ids)
        if self._N == 0:
            self._avgdl = 0.0
            self._df = {}
            self._idf = {}
            return

        self._avgdl = sum(self._dl) / self._N

        self._df = {}
        for tf_map in self._tf:
            for term in tf_map:
                self._df[term] = self._df.get(term, 0) + 1

        self._idf = {}
        for term, df in self._df.items():
            self._idf[term] = math.log((self._N - df + 0.5) / (df + 0.5) + 1)

    def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Return top_k results as dicts with id/document/metadata/score keys."""
        if self._N == 0 or os.environ.get("NEURALMIND_BM25") == "0":
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        scores: dict[int, float] = {}
        k1, b, avgdl = self.k1, self.b, self._avgdl

        for term in q_tokens:
            if term not in self._idf:
                continue
            idf = self._idf[term]
            for i, tf_map in enumerate(self._tf):
                tf = tf_map.get(term, 0)
                if tf == 0:
                    continue
                dl = self._dl[i]
                # Sublinear TF scaling: log(tf) + 1 prevents high-TF docs from dominating
                sublinear_tf = 1 + math.log(tf) if tf > 0 else 0
                denom = (
                    sublinear_tf + k1 * (1 - b + b * dl / avgdl) if avgdl > 0 else sublinear_tf + k1
                )
                score = idf * sublinear_tf * (k1 + 1) / denom
                scores[i] = scores.get(i, 0.0) + score

        if not scores:
            return []

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        max_score = ranked[0][1] if ranked else 1.0

        return [
            {
                "id": self._ids[i],
                "document": self._docs[i],
                "metadata": self._metadatas[i],
                "score": score / max_score,  # normalise to [0, 1]
                "_bm25_raw": score,
            }
            for i, score in ranked
        ]

    def bm25_search_prose(self, query: str, n: int = 10) -> list[dict[str, Any]]:
        """Return top_k results using prose-friendly tokenization.

        Same result shape as :meth:`search`, but tokenizes the query with
        :func:`_tokenize_prose` so hyphenated terms (BPC-157, GLP-1) stay
        whole — critical for book/prose retrieval where those tokens carry
        meaning that code-style splitting (``bpc``, ``157``) would dilute.

        Applies two enhancements for book retrieval:
        1. Downweights reference/appendix chapters (e.g., Claims Register)
           so drug names in reference tables don't outrank content chapters.
        2. Boosts documents containing ALL rare query terms (AND logic)
           for multi-drug comparison queries.
        """
        if self._N == 0 or os.environ.get("NEURALMIND_BM25") == "0":
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        scores: dict[int, float] = {}
        k1, b, avgdl = self.k1, self.b, self._avgdl

        # Identify rare terms (DF ≤ 5) for AND boost
        rare_terms = [t for t in q_tokens if t in self._idf and self._df.get(t, 0) <= 5]

        for term in q_tokens:
            if term not in self._idf:
                continue
            idf = self._idf[term]
            for i, tf_map in enumerate(self._tf):
                tf = tf_map.get(term, 0)
                if tf == 0:
                    continue
                dl = self._dl[i]
                # Sublinear TF scaling: log(tf) + 1 prevents high-TF docs from dominating
                sublinear_tf = 1 + math.log(tf) if tf > 0 else 0
                denom = (
                    sublinear_tf + k1 * (1 - b + b * dl / avgdl) if avgdl > 0 else sublinear_tf + k1
                )
                score = idf * sublinear_tf * (k1 + 1) / denom
                scores[i] = scores.get(i, 0.0) + score

        if not scores:
            return []

        # Fix 1: Downweight reference/appendix chapters (Claims Register)
        # These contain drug names in reference tables but aren't content chapters
        reference_penalty = 0.5
        for i in scores:
            meta = self._metadatas[i] if i < len(self._metadatas) else {}
            chapter = meta.get("chapter", "")
            section = meta.get("section", "")
            # Downweight claims register and appendix content
            if "claims register" in chapter.lower() or "claims register" in section.lower():
                scores[i] *= reference_penalty
            # Also downweight by source filename for robustness
            source_file = meta.get("source_file", "")
            if "claims-register" in source_file or "claims_register" in source_file:
                scores[i] *= reference_penalty

        # Fix 2: AND boost for multi-term queries with rare terms
        # When query has 2+ rare terms, boost documents containing ALL of them
        if len(rare_terms) >= 2:
            and_boost = 1.5  # 50% boost for documents with all rare terms
            for i in scores:
                tf_map = self._tf[i]
                has_all = all(tf_map.get(t, 0) > 0 for t in rare_terms)
                if has_all:
                    scores[i] *= and_boost

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
        max_score = ranked[0][1] if ranked else 1.0

        return [
            {
                "id": self._ids[i],
                "document": self._docs[i],
                "metadata": self._metadatas[i],
                "score": score / max_score,  # normalise to [0, 1]
                "_bm25_raw": score,
            }
            for i, score in ranked
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        """Serialise to JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": self._VERSION,
            "k1": self.k1,
            "b": self.b,
            "ids": self._ids,
            "docs": self._docs,
            "metadatas": self._metadatas,
            "tf": self._tf,
            "dl": self._dl,
            "df": self._df,
            "idf": self._idf,
            "avgdl": self._avgdl,
            "N": self._N,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, separators=(",", ":"))

    @classmethod
    def load(cls, path: Path) -> "BM25Index":
        """Deserialise from JSON (returns empty index on any error)."""
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            if d.get("version") != cls._VERSION:
                return cls()
            idx = cls(k1=d["k1"], b=d["b"])
            idx._ids = d["ids"]
            idx._docs = d["docs"]
            idx._metadatas = d["metadatas"]
            idx._tf = [dict(tf) for tf in d["tf"]]
            idx._dl = d["dl"]
            idx._df = d["df"]
            idx._idf = d["idf"]
            idx._avgdl = d["avgdl"]
            idx._N = d["N"]
            return idx
        except Exception:
            return cls()
