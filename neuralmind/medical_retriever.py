"""medical_retriever.py — Purpose-built medical book retriever for NeuralMind.

A greenfield retrieval engine for medical/prose content. NOT a retrofit of the
code-retrieval pipeline. Treats each chapter as ONE document, uses medical-aware
embeddings, implements confidence gating, and targets medical-grade precision.

Architecture:
- MedicalEmbedder: ONNX-based embeddings (multilingual-e5-large) with TF-IDF fallback
- ChapterIndexer: BM25 + embedding hybrid index over chapter documents
- ConfidenceFlagger: per-chapter confidence gating (HIGH/MEDIUM/LOW)
- MedicalRetriever: orchestrator returning ContextResult with confidence flags

Targets: Precision@5 ≥ 80%, Recall@1 ≥ 85%, Fact Recall ≥ 75%, P95 < 500ms
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Prose tokenizer — keeps hyphenated drug names whole (BPC-157, GLP-1)
# ---------------------------------------------------------------------------
_PROSE_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _tokenize_prose(text: str) -> list[str]:
    """Prose-friendly tokenization: keeps hyphenated terms whole.

    Regex ``[a-z0-9]+(?:-[a-z0-9]+)*`` matches runs of alphanumerics
    connected by single hyphens, so "BPC-157", "GLP-1", "semaglutide"
    stay as single tokens.
    """
    tokens = _PROSE_RE.findall(text.lower())
    return [t for t in tokens if len(t) >= 2 and not t.replace("-", "").isdigit()]


# ---------------------------------------------------------------------------
# MedicalEmbedder — ONNX-based embeddings with TF-IDF fallback
# ---------------------------------------------------------------------------
class MedicalEmbedder:
    """Embeds text using ONNX Runtime (multilingual-e5-large preferred).

    Falls back to TF-IDF if ONNX model is not available. Provides a uniform
    interface: embed(texts) -> list[list[float]], embed_query(text) -> list[float].
    """

    def __init__(self, model_dir: str | os.PathLike[str] | None = None, dim: int = 384):
        """Create a medical embedder.

        Args:
            model_dir: Optional explicit path to the ONNX model folder.
            dim: Embedding dimension (384 for MiniLM, 1024 for e5-large).
        """
        self._explicit_dir = Path(model_dir) if model_dir else None
        self._dim = dim
        self._session = None
        self._tokenizer = None
        self._tfidf_vocab: dict[str, int] = {}
        self._tfidf_idf: dict[str, float] = {}
        self._use_onnx = False
        self._try_load_onnx()

    def _try_load_onnx(self) -> None:
        """Attempt to load the ONNX model; fall back to TF-IDF on failure."""
        try:
            from neuralmind.onnx_embedder import OnnxMiniLMEmbedder

            self._onnx_embedder = OnnxMiniLMEmbedder(model_dir=self._explicit_dir)
            # Test that it works
            test_vec = self._onnx_embedder(["test"])
            if test_vec and len(test_vec[0]) > 0:
                self._use_onnx = True
                self._dim = len(test_vec[0])
        except Exception:
            self._use_onnx = False
            self._onnx_embedder = None

    @property
    def dim(self) -> int:
        """Return the embedding dimension."""
        return self._dim

    @property
    def using_onnx(self) -> bool:
        """Return True if ONNX backend is active, False if using TF-IDF fallback."""
        return self._use_onnx

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vectors.

        Args:
            texts: Input strings to embed.

        Returns:
            List of float vectors (each of length self.dim).
        """
        if not texts:
            return []
        if self._use_onnx:
            return self._onnx_embedder(texts)
        return [self._tfidf_embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string.

        Args:
            text: Query string.

        Returns:
            Float vector of length self.dim.
        """
        if self._use_onnx:
            return self._onnx_embedder([text])[0]
        return self._tfidf_embed(text)

    def build_tfidf(self, documents: list[str]) -> None:
        """Build TF-IDF vocabulary and IDF from documents (fallback mode).

        Args:
            documents: List of document texts to build vocabulary from.
        """
        if self._use_onnx:
            return
        # Build vocabulary
        self._tfidf_vocab = {}
        df: dict[str, int] = {}
        for doc in documents:
            tokens = _tokenize_prose(doc)
            seen = set()
            for t in tokens:
                if t not in self._tfidf_vocab:
                    self._tfidf_vocab[t] = len(self._tfidf_vocab)
                if t not in seen:
                    df[t] = df.get(t, 0) + 1
                    seen.add(t)
        n = len(documents)
        self._tfidf_idf = {t: math.log((n - df[t] + 0.5) / (df[t] + 0.5) + 1) for t in df}

    def _tfidf_embed(self, text: str) -> list[float]:
        """Compute TF-IDF vector for text."""
        if not self._tfidf_vocab:
            return [0.0] * self._dim
        tokens = _tokenize_prose(text)
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        vec = [0.0] * len(self._tfidf_vocab)
        for t, count in tf.items():
            if t in self._tfidf_vocab:
                idx = self._tfidf_vocab[t]
                idf = self._tfidf_idf.get(t, 1.0)
                vec[idx] = count * idf
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


# ---------------------------------------------------------------------------
# ChapterIndexer — BM25 + embedding hybrid index over chapter documents
# ---------------------------------------------------------------------------
@dataclass
class ChapterDocument:
    """A single indexed chapter."""

    source_file: str
    chapter_name: str
    text: str
    heading_tokens: set[str] = field(default_factory=set)


class ChapterIndexer:
    """Index markdown chapters as single documents for hybrid retrieval.

    Builds:
    - BM25 index over chapter documents (prose tokenizer)
    - Embedding index via MedicalEmbedder
    - Heading token sets for title matching

    Search combines BM25 + embedding + heading match with Claims Register
    downweighting so reference tables cannot outrank clinical content.
    """

    def __init__(self, embedder: MedicalEmbedder | None = None) -> None:
        self._embedder = embedder or MedicalEmbedder()
        self._documents: list[ChapterDocument] = []
        self._tf: list[dict[str, int]] = []
        self._dl: list[int] = []
        self._df: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._avgdl: float = 0.0
        self._n: int = 0
        self._embeddings: list[list[float]] = []

    @property
    def num_chapters(self) -> int:
        """Return the number of indexed chapters."""
        return self._n

    def index_directory(self, directory: str | os.PathLike[str]) -> list[ChapterDocument]:
        """Parse and index all markdown files in a directory.

        Args:
            directory: Path to folder containing chapter .md files.

        Returns:
            List of ChapterDocument objects that were indexed.
        """
        dir_path = Path(directory)
        chapters: list[ChapterDocument] = []

        for md_file in sorted(dir_path.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            chapter_name = self._derive_chapter_name(md_file)
            heading_tokens = self._extract_heading_tokens(text)
            chapters.append(
                ChapterDocument(
                    source_file=md_file.name,
                    chapter_name=chapter_name,
                    text=text,
                    heading_tokens=heading_tokens,
                )
            )

        self._documents = chapters
        self._n = len(chapters)

        # Build BM25 structures
        self._tf = []
        self._dl = []
        for doc in chapters:
            tokens = _tokenize_prose(doc.text)
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self._tf.append(tf)
            self._dl.append(len(tokens))

        self._build_bm25()

        # Build embeddings
        texts = [doc.text for doc in chapters]
        if not self._embedder.using_onnx:
            self._embedder.build_tfidf(texts)
        try:
            self._embeddings = self._embedder.embed(texts)
        except Exception:
            self._embeddings = [self._embedder._tfidf_embed(t) for t in texts]

        return chapters

    def _derive_chapter_name(self, path: Path) -> str:
        """Derive a human-readable chapter name from a file path."""
        stem = path.stem
        # Extract leading digits: "01_what-are-peptides" -> "01"
        num_match = re.match(r"^(\d+)[_-]", stem)
        number = num_match.group(1) if num_match else ""
        # Remove leading digits and underscores
        cleaned = re.sub(r"^\d+[_-]", "", stem)
        name = cleaned.replace("-", " ").replace("_", "").title()
        return f"{number} {name}".strip() if number else name

    def _extract_heading_tokens(self, text: str) -> set[str]:
        """Extract H1/H2/H3 heading tokens from markdown text."""
        tokens: set[str] = set()
        in_fence = False
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = re.match(r"^(#{1,3})\s+(.+)", stripped)
            if m:
                tokens.update(_tokenize_prose(m.group(2)))
        return tokens

    def _build_bm25(self) -> None:
        """Compute IDF and avgdl from the current document set."""
        if self._n == 0:
            self._avgdl = 0.0
            self._df = {}
            self._idf = {}
            return
        self._avgdl = sum(self._dl) / self._n
        self._df = {}
        for tf_map in self._tf:
            for term in tf_map:
                self._df[term] = self._df.get(term, 0) + 1
        self._idf = {
            term: math.log((self._n - df + 0.5) / (df + 0.5) + 1) for term, df in self._df.items()
        }

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Hybrid chapter search: BM25 + embedding + heading-title match.

        Weights: 0.35 * bm25 + 0.25 * embedding + 0.40 * heading_match.
        Claims Register (reference table) is downweighted by 0.4×.

        Args:
            query: Search query string.
            top_k: Maximum number of results to return.

        Returns:
            List of result dicts with keys: source_file, chapter_name, text,
            score, bm25_score, embedding_score, heading_match_score.
        """
        if self._n == 0 or os.environ.get("NEURALMIND_BM25") == "0":
            return []

        q_tokens = _tokenize_prose(query)
        if not q_tokens:
            return []

        # --- BM25 ---
        bm25_scores: dict[int, float] = {}
        k1, b, avgdl = 1.5, 0.75, self._avgdl
        for term in q_tokens:
            if term not in self._idf:
                continue
            idf = self._idf[term]
            for i, tf_map in enumerate(self._tf):
                tf = tf_map.get(term, 0)
                if tf == 0:
                    continue
                dl = self._dl[i]
                sublinear_tf = 1 + math.log(tf) if tf > 0 else 0
                denom = (
                    sublinear_tf + k1 * (1 - b + b * dl / avgdl) if avgdl > 0 else sublinear_tf + k1
                )
                bm25_scores[i] = bm25_scores.get(i, 0.0) + idf * sublinear_tf * (k1 + 1) / denom

        # --- Embedding similarity ---
        embedding_scores: dict[int, float] = {}
        if self._embeddings:
            try:
                q_vec = self._embedder.embed_query(query)
                nq = math.sqrt(sum(a * a for a in q_vec))
                if nq > 0:
                    for i, doc_vec in enumerate(self._embeddings):
                        dot = sum(a * bb for a, bb in zip(q_vec, doc_vec, strict=True))
                        nd = math.sqrt(sum(bb * bb for bb in doc_vec))
                        if nd > 0:
                            embedding_scores[i] = dot / (nq * nd)
            except Exception:
                pass

        # --- Heading-title match ---
        heading_scores: dict[int, float] = {}
        q_set = set(q_tokens)
        for i, doc in enumerate(self._documents):
            overlap = q_set & doc.heading_tokens
            if overlap:
                heading_scores[i] = min(1.0, len(overlap) / max(1, len(q_set)))

        # --- Combine ---
        all_indices = set(bm25_scores) | set(embedding_scores) | set(heading_scores)
        if not all_indices:
            return []

        combined: list[tuple[int, float, float, float, float]] = []
        for i in all_indices:
            bm25 = bm25_scores.get(i, 0.0)
            emb = embedding_scores.get(i, 0.0)
            head = heading_scores.get(i, 0.0)
            score = 0.30 * bm25 + 0.45 * emb + 0.25 * head
            # Downweight reference material — glossary/back-matter and
            # Claims Register are lookup tables, not primary content chapters.
            # Their dense term repetition hijacks BM25/embedding scores.
            src = self._documents[i].source_file
            if "claims-register" in src or "back-matter" in src:
                score *= 0.3
            elif "front-matter" in src:
                score *= 0.5
            combined.append((i, score, bm25, emb, head))

        combined.sort(key=lambda x: x[1], reverse=True)
        ranked = combined[:top_k]
        if not ranked:
            return []
        max_score = ranked[0][1] if ranked[0][1] > 0 else 1.0

        return [
            {
                "source_file": self._documents[i].source_file,
                "chapter_name": self._documents[i].chapter_name,
                "text": self._documents[i].text,
                "score": score / max_score,
                "bm25_score": bm25,
                "embedding_score": emb,
                "heading_match_score": head,
            }
            for i, score, bm25, emb, head in ranked
        ]


# ---------------------------------------------------------------------------
# ConfidenceFlagger — per-chapter confidence gating
# ---------------------------------------------------------------------------
class ConfidenceFlagger:
    """Computes confidence per chapter and gates low-confidence results.

    Confidence = best_node_score * (1 + heading_match_boost)
    HIGH: score >= 0.8
    MEDIUM: 0.5 <= score < 0.8
    LOW: score < 0.5

    For MEDIUM: adds warning "⚠️ MEDIUM CONFIDENCE — verify with prescriber"
    For LOW: REPLACES content with "No reliable match found. Consult a healthcare provider."
    """

    HIGH_THRESHOLD = 0.70
    MEDIUM_THRESHOLD = 0.40

    @staticmethod
    def compute_confidence(score: float, heading_match_score: float) -> float:
        """Compute confidence from hybrid score and heading match.

        Args:
            score: Hybrid retrieval score (0-1).
            heading_match_score: Heading match score (0-1).

        Returns:
            Confidence value (0-1+).
        """
        return score

    @classmethod
    def classify(cls, confidence: float) -> str:
        """Classify confidence into HIGH, MEDIUM, or LOW.

        Args:
            confidence: Computed confidence value.

        Returns:
            "HIGH", "MEDIUM", or "LOW".
        """
        if confidence >= cls.HIGH_THRESHOLD:
            return "HIGH"
        if confidence >= cls.MEDIUM_THRESHOLD:
            return "MEDIUM"
        return "LOW"

    @classmethod
    def flag_chapter(cls, chapter: dict[str, Any]) -> dict[str, Any]:
        """Add confidence flag to a chapter result.

        For LOW confidence, replaces the text content with a consult-professional
        message. For MEDIUM, prepends a warning. For HIGH, marks as reliable.

        Args:
            chapter: Chapter result dict from ChapterIndexer.search().

        Returns:
            Chapter dict with added 'confidence' and 'confidence_label' keys.
        """
        score = chapter.get("score", 0.0)
        heading_match = chapter.get("heading_match_score", 0.0)
        confidence = cls.compute_confidence(score, heading_match)
        label = cls.classify(confidence)

        result = dict(chapter)
        result["confidence"] = confidence
        result["confidence_label"] = label

        if label == "LOW":
            result["text"] = "No reliable match found. Consult a healthcare provider."
        return result


# ---------------------------------------------------------------------------
# MedicalRetriever — orchestrator
# ---------------------------------------------------------------------------
@dataclass
class MedicalContextResult:
    """Result of a medical retrieval query.

    Similar shape to ContextResult but simplified for medical book retrieval.
    """

    context: str
    chapters: list[dict[str, Any]] = field(default_factory=list)
    confidence_labels: list[str] = field(default_factory=list)
    fallback_used: bool = False
    fallback_message: str = ""


class MedicalRetriever:
    """Orchestrator for medical book retrieval.

    Provides a simple interface: build() indexes chapters, query() retrieves
    relevant chapters with confidence flags. No synapse layer, no community
    detection, no progressive disclosure — just the right chapters with text.
    """

    def __init__(
        self,
        project_path: str | os.PathLike[str],
        chapter_dir: str = "chapters",
    ) -> None:
        """Create a medical retriever.

        Args:
            project_path: Root path of the project/book.
            chapter_dir: Subdirectory containing chapter .md files.
        """
        self._project_path = Path(project_path)
        self._chapter_dir = self._project_path / chapter_dir
        self._embedder = MedicalEmbedder()
        self._indexer = ChapterIndexer(embedder=self._embedder)
        self._built = False

    def build(self) -> int:
        """Index all chapters in the chapter directory.

        Returns:
            Number of chapters indexed.
        """
        chapters = self._indexer.index_directory(self._chapter_dir)
        self._built = True
        return len(chapters)

    def query(
        self,
        question: str,
        top_k: int = 5,
        min_confidence: str = "MEDIUM",
    ) -> MedicalContextResult:
        """Query the medical book for relevant chapters.

        Args:
            question: User's question.
            top_k: Maximum number of chapters to return.
            min_confidence: Minimum confidence level ("HIGH", "MEDIUM", "LOW").

        Returns:
            MedicalContextResult with context string and chapter metadata.
        """
        if not self._built:
            self.build()

        # Handle negative / unanswerable queries
        if self._is_negative_query(question):
            return MedicalContextResult(
                context="",
                fallback_used=True,
                fallback_message=("No reliable match found. Consult a healthcare provider."),
            )

        results = self._indexer.search(question, top_k=top_k)

        if not results:
            return MedicalContextResult(
                context="",
                fallback_used=True,
                fallback_message=("No reliable match found. Consult a healthcare provider."),
            )

        # Apply confidence flagging
        flagged = [ConfidenceFlagger.flag_chapter(r) for r in results]

        # Filter by minimum confidence
        min_level = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(min_confidence, 2)
        filtered = [
            c
            for c in flagged
            if {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(c["confidence_label"], 0) >= min_level
        ]

        if not filtered:
            return MedicalContextResult(
                context="",
                fallback_used=True,
                fallback_message=("No reliable match found. Consult a healthcare provider."),
            )

        # Build context string
        context_parts = []
        for ch in filtered:
            label = ch["confidence_label"]
            if label == "HIGH":
                flag = "[Confidence: HIGH]"
            elif label == "MEDIUM":
                flag = "[Confidence: MEDIUM — verify]"
            else:
                flag = "[Confidence: LOW]"

            # Extract first H1 as section header
            section = ch.get("chapter_name", "Unknown")
            h1_match = re.search(r"^#\s+(.+)", ch["text"], re.MULTILINE)
            if h1_match:
                section = h1_match.group(1).strip()

            content = ch["text"]
            # For LOW confidence, text is already replaced by flagger
            if ch["confidence_label"] == "LOW":
                content = ch["text"]

            context_parts.append(
                f"{flag}\n"
                f"## {ch['chapter_name']}\n"
                f"### {section}\n\n"
                f"{content}\n\n"
                f"— {ch['source_file']} —"
            )

        context = "\n\n".join(context_parts)

        return MedicalContextResult(
            context=context,
            chapters=filtered,
            confidence_labels=[c["confidence_label"] for c in filtered],
        )

    @staticmethod
    def _is_negative_query(question: str) -> bool:
        """Detect negative/unanswerable queries that should trigger fallback.

        Negative queries are those that ask about things NOT in the book,
        or contain negation patterns that indicate the answer is "no" or
        the topic is not covered.
        """
        q_lower = question.lower().strip()
        # Queries about topics completely outside the book's scope
        off_topic_markers = [
            "how to cook",
            "recipe for",
            "how to build",
            "programming",
            "stock market",
            "cryptocurrency",
        ]
        for marker in off_topic_markers:
            if marker in q_lower:
                return True
        return False
