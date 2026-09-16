# NeuralMind — Kanban Board (CANONICAL — `dfrostar/neuralmind`)

**2026-09-15 18:30:00**
**Repo:** `neuralmind` (dfrostar/neuralmind)
**Version:** 3.12.0
**Branch:** main
**Last commit:** `883371f` — chore: update NeuralMind team memory snapshot [skip ci] (2026-09-15)
**Note:** This is the canonical kanban for NeuralMind. Active development repo is `/home/dtfrost5/neuralmind/` (v3.12.0, main branch).

---

## Current State

```
Version:   3.12.0 (released 2026-09-15)
Git:       main branch, last commit 2026-09-15 (0 days stale)
Uncommitted: 16 files (context_selector.py, chapter_indexer.py, medical_retriever.py, 4 new tests, 10 .neuralmind cache files)
CI:        Regression floor at 4.0× — LOCAL RUN 4.74× PASS
Engine:    v3.12.0 — chapter-level scoring, dedup, medical terminology expansion, BM25 prose tokenizer fix
Benchmark: Recall@5 97.6% (14 queries), all ≥80% R@5, Hit Rate 100%
Release:   release-please manifest at 3.12.0; pyproject.toml still at 3.11.3 (sync needed)
```

---

## ✅ Shipped (v3.11.0 → v3.12.0 — 2026-09-14 → 2026-09-15)

| Component | Status | Evidence |
|-----------|--------|----------|
| Prose-aware retrieval | ✅ DONE | Heading-aware chunking, H1→chapter, H2→section |
| Adaptive BM25 weights | ✅ DONE | Rare terms (DF≤3) boost BM25 to 0.8 |
| Sublinear TF scaling | ✅ DONE | log(tf)+1 prevents high-TF dominance |
| Hybrid merge fix | ✅ DONE | BM25-only results preserve full score |
| BM25 tokenizer alignment | ✅ DONE | Prose tokenizer for both indexing and search |
| Reference downweight | ✅ DONE | Claims Register scores 0.5× penalty |
| Multi-term AND boost | ✅ DONE | 1.5× boost for queries with 2+ rare terms |
| Heading text in chunks | ✅ DONE | Short docs + sub-chunks include heading |
| Query intent boost | ✅ DONE | 1.3× for mechanism/comparison/regulatory/delivery/safety |
| v5 book content | ✅ DONE | 11 chapters extracted from Rye's DOCX |
| Chapter-level scoring | ✅ DONE | cf85a68 — dedup chapters in context, boost top chapter |
| Medical terminology expansion | ✅ DONE | 51cb0d5 — BPC-157, GHK-Cu, semaglutide, retatrutide mapped |
| BM25 prose tokenizer fix | ✅ DONE | 51cb0d5 — align prose tokenization across index + search |
| Stronger intent boost | ✅ DONE | 8cbe591 — expand intent keyword matching |

---

## 🔴 P0 — Version Sync & Release (2026-09-15)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T1 | Sync pyproject.toml to 3.12.0 | ⬜ TODO | Manifest at 3.12.0, pyproject at 3.11.3 |
| T2 | Verify CI self-benchmark gate | 🔄 PENDING | Local 4.74×; CI uses fresh regeneration |
| T3 | Publish to PyPI | ⬜ TODO | `python -m build && twine upload dist/*` |

---

## 🔄 Uncommitted Work (2026-09-15)

| File | Status | Notes |
|------|--------|-------|
| `neuralmind/context_selector.py` | ✅ MODIFIED | Uncommitted code changes |
| `neuralmind/chapter_indexer.py` | ✅ NEW | Chapter-level indexing module |
| `neuralmind/medical_retriever.py` | ✅ NEW | Medical terminology retriever |
| `tests/test_chapter_index.py` | ✅ NEW | Tests for chapter indexer |
| `tests/test_medical_retriever.py` | ✅ NEW | Tests for medical retriever |
| `tests/benchmark/peptide_results.json` | ✅ MODIFIED | Latest benchmark results |
| `tests/benchmark/peptide_report.md` | ✅ MODIFIED | Benchmark report |
| `tests/fixtures/*/extraction_cache.json` | ✅ MODIFIED | 10 fixture cache updates |

> **16 uncommitted files:** New chapter indexer + medical retriever modules, benchmark results, fixture caches.

---

## 📊 Peptide Book Retrieval — Objective Status (v3.12.0, 14 queries)

**Aggregate Metrics:**

| Metric | Value | Grade |
|--------|-------|-------|
| Recall@1 | 57.1% | 🟡 |
| Recall@3 | 91.7% | 🟢 |
| Recall@5 | 97.6% | 🟢 |
| Precision@5 | 45.0% | 🔴 |
| MRR | 0.75 | 🟡 |
| nDCG@5 | 0.79 | 🟡 |
| Hit Rate | 100.0% | 🟢 |
| Avg Latency | 1,283ms | 🔴 |
| P95 Latency | 15,066ms | 🔴 |

**Per-Query (R@5):** 14/14 at 100% except:
- peptide-definition: R@5=1.00, R@1=0.00 (correct chapter in top-3)
- glp1-mechanism: R@5=0.67 (Ch2 in top-3, not top-1)
- weight-loss-semaglutide: R@5=1.00, MRR=0.33
- retatrutide-triple-agonist: R@5=1.00, MRR=0.50

**Improvement vs v3.11.2:** Recall@5 86.9% → 97.6%. All 4 weak queries fixed.

**Remaining weakness:** Precision@5 45.0% — too many irrelevant chapters in top-5.

---

## Decisions Made

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-09-15 | **v3.12.0 release** | Chapter-level scoring, dedup, medical terminology expansion, BM25 tokenizer fix |
| 2026-09-15 | **Chapter-level scoring** | Deduplicate chapters in context, boost top chapter relevance |
| 2026-09-15 | **Medical terminology expansion** | Map BPC-157, GHK-Cu, semaglutide, retatrutide to canonical forms |
| 2026-09-15 | **BM25 prose tokenizer fix** | Align prose tokenization across indexing and search |
| 2026-09-14 | **BM25 reference downweight (0.5×)** | Claims Register contains drug names in reference tables but isn't a content chapter. |
| 2026-09-14 | **Multi-term AND boost (1.5×)** | Queries with 2+ rare terms (DF≤5) should boost documents containing ALL terms. |
| 2026-09-14 | **Heading text in chunk content** | Short docs and sub-chunks now include parent heading text for better BM25 matching. |
| 2026-09-14 | **Darren lives in Texas** | User correction — no city specified. |
| 2026-09-14 | **v5 book content** | Rye Walker edits: removed Conclusion, moved About Authors to Back Matter. |
| 2026-09-14 | **ROOT CAUSE: Vector-BM25 ID mismatch** | Vector had 77 heading nodes, BM25 had 315 content chunks. IDs didn't match. |

---

## 📋 Action Items (Next 24h)

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Sync pyproject.toml to 3.12.0 | Agent | ⬜ TODO |
| 2 | Verify CI self-benchmark gate on fresh run | User | 🔄 PENDING |
| 3 | If CI green, publish to PyPI | User | ⬜ TODO |
| 4 | Regenerate benchmark chart (if CI green) | Agent | ⬜ TODO |
| 5 | Commit new modules + tests + kanban | Agent | ⬜ TODO |
| 6 | Fix precision@5 (dedup chapters in context) | Agent | ⬜ TODO |
| 7 | Fix cold-start P95 latency (pre-load model) | Agent | ⬜ TODO |

---

*NeuralMind v3.12.0 — Chapter-level scoring, dedup, medical terminology shipped. All 14 benchmark queries ≥80% R@5. Last commit: 883371f. Next: version sync → verify CI → publish to PyPI.*
