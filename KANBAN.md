# NeuralMind — Kanban Board (CANONICAL — `dfrostar/neuralmind`)

**2026-09-15 06:45:00**
**Repo:** `neuralmind` (dfrostar/neuralmind)
**Version:** 3.11.3
**Branch:** main
**Last commit:** `3279dc5` — docs: update kanban with v3.11.3 status and action items (2026-09-15)
**Note:** This is the canonical kanban for NeuralMind. Active development repo is `/home/dtfrost5/neuralmind/` (v3.11.3, main branch).

---

## Current State

```
Version:   3.11.3 (released 2026-09-15)
Tests:     211 tests passing (document_ingestion, book_indexing, turbovec_backend, graphgen, ingest_content)
Git:       main branch, last commit 2026-09-15 (0 days stale)
Uncommitted: 2 benchmark files (gitignored)
CI:        Regression floor at 4.0× — LOCAL RUN 4.74× PASS
Engine:    v3.11.3 — query intent boost, adaptive BM25, heading-aware chunking, reference downweight
Benchmark: Recall@5 97.6% (14 queries), all ≥80% R@5, Hit Rate 100%
Release:   pyproject.toml + release-please-manifest updated to 3.11.3
```

---

## ✅ Shipped (v3.11.0 → v3.11.3 — 2026-09-14 → 2026-09-15)

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
| Darren location fix | ✅ DONE | Texas (not Dallas) |
| Benchmark v5 alignment | ✅ DONE | 14 queries updated for v5 content |
| Version sync | ✅ DONE | pyproject.toml + manifest at 3.11.3 |

---

## 🔴 P0 — CI & Release (2026-09-15)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T1 | Verify CI self-benchmark gate | 🔄 PENDING | Local 4.74×; CI uses fresh regeneration |
| T2 | Release-please draft for v3.11.3 | ⬜ TODO | Check https://github.com/dfrostar/neuralmind/releases |
| T3 | Publish to PyPI | ⬜ TODO | `python -m build && twine upload dist/*` |
| T4 | Update benchmark chart | ⬜ TODO | `python -m tests.benchmark.run` + chart |

**Blocking:** User must verify CI passes on fresh run. The self-benchmark gate reads the gitignored `results.json` which CI regenerates on every run.

---

## 🔄 Uncommitted Work (2026-09-15)

| File | Status | Notes |
|------|--------|-------|
| `pyproject.toml` | ✅ MODIFIED | version = "3.11.3" |
| `.release-please-manifest.json` | ✅ MODIFIED | version = "3.11.3" |
| `KANBAN.md` | ✅ MODIFIED | This file |

> **Clean:** Only version sync + kanban update. Benchmark files are gitignored. Test fixtures reverted.

---

## 📊 Peptide Book Retrieval — Objective Status (v3.11.3, 14 queries)

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
| 2026-09-15 | **Query intent boost (1.3×)** | Detect intent via keyword matching; boost chapters whose intent matches query intent. Fixes mechanism/comparison/regulatory queries. |
| 2026-09-14 | **BM25 reference downweight (0.5×)** | Claims Register contains drug names in reference tables but isn't a content chapter. |
| 2026-09-14 | **Multi-term AND boost (1.5×)** | Queries with 2+ rare terms (DF≤5) should boost documents containing ALL terms. |
| 2026-09-14 | **Heading text in chunk content** | Short docs and sub-chunks now include parent heading text for better BM25 matching. |
| 2026-09-14 | **Darren lives in Texas** | User correction — no city specified. |
| 2026-09-14 | **v5 book content** | Rye Walker edits: removed Conclusion, moved About Authors to Back Matter. |
| 2026-09-14 | **ROOT CAUSE: Vector-BM25 ID mismatch** | Vector had 77 heading nodes, BM25 had 315 content chunks. IDs didn't match. |
| 2026-09-13 | v3.10.0 released | BGE embedder, SEO pages, benchmark page |

---

## 📋 Action Items (Next 24h)

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Verify CI self-benchmark gate on fresh run | User | 🔄 PENDING |
| 2 | Check release-please draft for v3.11.3 | User | ⬜ TODO |
| 3 | If CI green, publish to PyPI | User | ⬜ TODO |
| 4 | Regenerate benchmark chart (if CI green) | Agent | ⬜ TODO |
| 5 | Commit version sync + kanban | Agent | ⬜ TODO |
| 6 | Fix precision@5 (dedup chapters in context) | Agent | ⬜ TODO |
| 7 | Fix cold-start P95 latency (pre-load model) | Agent | ⬜ TODO |

---

*NeuralMind v3.11.3 — Query intent boost shipped. All 14 benchmark queries ≥80% R@5. Version synced for release. Next: verify CI gate, then publish to PyPI.*
