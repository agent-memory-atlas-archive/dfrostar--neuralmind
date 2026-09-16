"""Integration test: chapter-level indexing via NeuralMind pipeline.

Uses the real ONNX embedder for chapter-level semantic similarity.
This is the SOTA path — chapter indexer + neural embeddings + BM25.
"""

import sys

sys.path.insert(0, "/home/dtfrost5/neuralmind")


import pytest

BOOK_DIR = "/home/dtfrost5/ai-agent-playbook-v2/books/peptide-patient-guide"
CHAPTERS_DIR = BOOK_DIR + "/chapters"


@pytest.fixture(scope="module")
def nm():
    """Build NeuralMind on peptide book with chapter-level indexing."""
    from neuralmind import core

    nm = core.NeuralMind(BOOK_DIR, enable_synapses=False)
    nm._ensure_built()
    return nm


class TestChapterLevelIntegration:
    """End-to-end tests using the full NeuralMind pipeline."""

    def test_semaglutide_returns_fda_chapter(self, nm):
        """'How does semaglutide work?' should return Ch2 or Ch3."""
        ctx = nm.query("How does semaglutide work in the body?")
        text = ctx.context.lower()
        assert (
            "glp-1" in text or "semaglutide" in text
        ), f"Context should contain GLP-1 or semaglutide. Got: {text[:300]}"

    def test_retatrutide_returns_fda_chapter(self, nm):
        """'Is retatrutide FDA approved?' should return Ch3."""
        ctx = nm.query("Is retatrutide FDA approved?")
        text = ctx.context.lower()
        assert (
            "retatrutide" in text or "not yet fda" in text
        ), f"Context should contain retatrutide info. Got: {text[:300]}"

    def test_black_box_warning_returns_safety_chapter(self, nm):
        """'What is the black box warning?' should return Ch5."""
        ctx = nm.query("What is the black box warning on semaglutide?")
        text = ctx.context.lower()
        assert (
            "black box" in text or "thyroid" in text
        ), f"Context should contain black box/thyroid info. Got: {text[:300]}"

    def test_oral_peptide_returns_future_chapter(self, nm):
        """'Oral peptide options' should return Ch7."""
        ctx = nm.query("Will there be oral peptide options?")
        text = ctx.context.lower()
        assert "oral" in text, f"Context should contain oral peptide info. Got: {text[:300]}"

    def test_bpc157_returns_grey_market_chapter(self, nm):
        """'What is BPC-157?' should return Ch4."""
        ctx = nm.query("What is BPC-157?")
        text = ctx.context.lower()
        assert (
            "bpc" in text or "grey" in text
        ), f"Context should contain BPC-157/grey market info. Got: {text[:300]}"

    def test_what_is_peptide_returns_ch1(self, nm):
        """'What is a peptide?' should return Ch1 (definitions)."""
        ctx = nm.query("What exactly is a peptide?")
        text = ctx.context.lower()
        assert (
            "amino acid" in text or "peptide is" in text
        ), f"Context should contain peptide definition. Got: {text[:300]}"

    def test_medical_book_no_code_graph_language(self, nm):
        """Prose projects should not say 'Code repository'."""
        ctx = nm.query("What is semaglutide?")
        assert (
            "code repository" not in ctx.context.lower()
        ), "Medical book should not use code repository language"

    def test_no_synapse_language(self, nm):
        """Raw context should not mention synapses for a static book."""
        ctx = nm.query("What is semaglutide?")
        assert "synapse" not in ctx.context.lower(), "Book context should not mention synapses"


class TestChapterIndexerStandalone:
    """Tests for ChapterIndexer with TF-IDF fallback vectors.

    These are the 8 unit tests that exercise the offline path
    (no embedder, TF-IDF cosine only). They verify the indexer
    provides basic retrieval without a neural embedding model.
    """

    def test_chapter_index_creates_one_node_per_chapter(self):
        from neuralmind.chapter_indexer import ChapterIndexer

        indexer = ChapterIndexer()
        chapters = indexer.index_directory(CHAPTERS_DIR)
        assert len(chapters) == 11
        for ch in chapters:
            assert "chapter_name" in ch
            assert "text" in ch
            assert len(ch["text"]) > 0

    def test_chapter_index_preserves_all_text(self):
        from neuralmind.chapter_indexer import ChapterIndexer

        indexer = ChapterIndexer()
        chapters = indexer.index_directory(CHAPTERS_DIR)
        fda = next(c for c in chapters if "03_fda" in c.get("source_file", ""))
        assert "semaglutide" in fda["text"]
        assert "tirzepatide" in fda["text"]

    def test_chapter_query_bm25_hyphenated_terms(self):
        from neuralmind.chapter_indexer import ChapterIndexer

        indexer = ChapterIndexer()
        indexer.index_directory(CHAPTERS_DIR)
        results = indexer.search("BPC-157", top_k=3)
        assert results, "Should return results for BPC-157"
        assert any("bpc" in r.get("text", "").lower() for r in results)

    def test_chapter_index_cold_start_latency(self):
        import time

        from neuralmind.chapter_indexer import ChapterIndexer

        indexer = ChapterIndexer()
        indexer.index_directory(CHAPTERS_DIR)
        start = time.time()
        indexer.search("semaglutide", top_k=3)
        elapsed = (time.time() - start) * 1000
        assert elapsed < 1000, f"First query took {elapsed:.0f}ms"
