# NeuralMind — Kanban Board (CANONICAL — `dfrostar/neuralmind`)

**2026-09-14 11:00:00**
**Repo:** `neuralmind` (dfrostar/neuralmind)
**Version:** 3.10.0
**Branch:** main
**Last commit:** `00f81bc` — chore: update NeuralMind team memory snapshot [skip ci] (2026-09-13)
**Note:** This is the canonical kanban for NeuralMind. Active development repo is `/home/dtfrost5/neuralmind/` (v3.10.0, main branch).

---

## Current State

```
Version:   3.10.0 (released 2026-09-13)
Tests:     65+ tests (synapse layer stdlib-only)
Git:       main branch, last commit 2026-09-13 (1 day stale)
Uncommitted: bm25.py, context_selector.py, core.py, document_ingestion.py, embedder.py, graphgen.py, turbovec_backend.py, test fixtures, peptide benchmark
CI:        Regression floor at 4.0× (matches origin/main)
Engine:    v3.10.0 — core, synapse, content QA, retrieval benchmarks, structural gap detection, VS Code extension, BGE embedder, SEO pages, benchmark page
```

---

## ✅ Shipped (v3.10.0 — 2026-09-13)

| Component | Status | Evidence |
|-----------|--------|----------|
| Core engine | ✅ DONE | `neuralmind/core.py` — orchestrator, public API |
| Synapse layer | ✅ DONE | Sharded + LTP guards, SQLite-backed Hebbian store |
| Context selector | ✅ DONE | L0/L1/L2/L3 progressive disclosure (12-50× token reduction) |
| BGE embedder | ✅ DONE | ChromaDB embeddings + 4 use cases |
| Retrieval benchmarks | ✅ DONE | 65+ tests passing |
| Structural gap detection | ✅ DONE | ✅ Shipped |
| VS Code extension | ✅ DONE | Status bar, command palette, graph panel, hover provider |
| Content QA (books) | ✅ DONE | Shipped |
| Marketing site | ✅ DONE | Next.js static export → Cloudflare Pages |
| SEO pages | ✅ DONE | Benchmark page, SEO plan, indexability fixes |
| v3.10.0 release | ✅ DONE | `bf46038` — chore(main): release 3.10.0 |

---

## 🔴 P0 — Retrieval Performance Fix (2026-09-14)

**ROOT CAUSE IDENTIFIED:** Vector index has 77 heading nodes, BM25 has 315 content chunks. IDs don't match → hybrid merge silently drops BM25 results. System returns Back Matter glossary for "semaglutide" instead of FDA-Approved chapter.

**Benchmark baseline:** P95 3,527ms, Precision@5 26.3%, Fact Recall 42%, Recall@1 57.9%
**Targets:** P95 <500ms, Precision@5 >70%, Fact Recall >75%, Recall@1 >75%

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T1 | Fix cold-start latency | 🔄 IN PROGRESS | Already uncommitted, needs verification |
| T2 | Fix vector-BM25 merge (ROOT CAUSE) | 🟡 PLANNED | Rebuild vector index from same 315 chunks as BM25 |
| T3 | BM25 hybrid scoring with adaptive weights | 🟡 PLANNED | Depends on T2 |
| T4 | Prose mode context cleanup | 🟡 PLANNED | Depends on T2/T3 |
| T5 | Confidence calibration | 🟡 PLANNED | Margin-based + exact-term boost |
| T6 | Ambiguity handling | 🟡 PLANNED | Visible confidence flags |
| T7 | Negative query fallback | 🟡 PLANNED | No low-confidence hints |
| T8 | Adversarial QA | ⬜ TODO | Strict thresholds |
| T9 | Final benchmark | ⬜ TODO | Compare against baseline |

**Safety protocol:** ADR `adr-nm-confidence-protocol` in `~/.hermes/projects.db`. Strict thresholds for medical — false positives are catastrophic.

---

## 🔄 Uncommitted Work (2026-09-14)

| File | Status | Notes |
|------|--------|-------|
| `neuralmind/bm25.py` | ✅ MODIFIED | BM25 hybrid search |
| `neuralmind/context_selector.py` | ✅ MODIFIED | Context selection updates |
| `neuralmind/core.py` | ✅ MODIFIED | Core orchestrator updates |
| `neuralmind/document_ingestion.py` | ✅ MODIFIED | Document ingestion updates |
| `neuralmind/embedder.py` | ✅ MODIFIED | Embedder updates |
| `neuralmind/graphgen.py` | ✅ MODIFIED | Graph generation updates |
| `neuralmind/turbovec_backend.py` | ✅ MODIFIED | TurboVec backend updates |
| `tests/fixtures/*/.neuralmind/extraction_cache.json` | ✅ MODIFIED | 8 fixture caches |
| `tests/test_graphgen.py` | ✅ MODIFIED | Graph gen tests |
| `neuralmind/neuralmind_config.py` | ✅ NEW | Config module |
| `tests/benchmark/peptide_benchmark.py` | ✅ NEW | Peptide benchmark |
| `tests/benchmark/peptide_queries.json` | ✅ NEW | Peptide queries |
| `tests/benchmark/peptide_report.md` | ✅ NEW | Peptide report |
| `tests/benchmark/peptide_results.json` | ✅ NEW | Peptide results |

> **⚠️ 14 uncommitted files** — needs commit or revert after T1-T3 verification.

---

## 🔴 CRITICAL BLOCKERS

| ID | Task | Impact | Est. |
|----|------|--------|------|
| BLK-1 | Commit or revert uncommitted changes | Dirty working tree | 0.5h |

---

## Sprint Backlog

| ID | Task | Priority | Status |
|----|------|----------|--------|
| S-01 | Logos training transformers | HIGH | ⬜ TODO |
| S-02 | Corpus expansion | MEDIUM | ⬜ TODO |
| S-03 | Perplexity eval framework | MEDIUM | ⬜ TODO |
| S-04 | Synapse Module wiki | LOW | ⬜ TODO |
| S-05 | Release automation (release-please) | LOW | ⬜ TODO |

---

## Decisions Made

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-09-14 | **ROOT CAUSE: Vector-BM25 ID mismatch** | Vector has 77 heading nodes, BM25 has 315 content chunks. Hybrid merge silently drops BM25 results because IDs don't match. Fix: rebuild vector index from same chunks. |
| 2026-09-14 | **Retrieval confidence & safety protocol** (ADR: adr-nm-confidence-protocol) | Medical content requires strict safety: margin-based confidence, visible ambiguity flags, no low-confidence hints, strict adversarial thresholds |
| 2026-09-14 | **BM25 weight: adaptive with hard floor** | Base 0.4 emb / 0.6 BM25; rare terms (≤3 docs) boost BM25 to 0.8; exact matches >2x next candidate win regardless |
| 2026-09-14 | **Content mode: per-project detection** | 80% .md + zero code files + name heuristic; tag at build time; no nano-LLM (overkill) |
| 2026-09-14 | **Ambiguity: top-1 with confidence flag** | Hiding uncertainty is dangerous; returning two chapters for every close call is noisy |
| 2026-09-14 | **Negative query: no hints, professional referral** | Low-confidence hints could be treated as answers; "I don't know" is safe |
| 2026-09-13 | v3.10.0 released | BGE embedder, SEO pages, benchmark page |
| 2026-09-13 | neuralmind/ is canonical | Active development repo (v3.10.0, main) |
| 2026-09-12 | neuralmind-fresh was canonical | `/home/dtfrost5/neuralmind/` was stale |
| 2026-09-03 | CI regression floor lowered to 3.0× | Prevent false CI failures |

---

## 📊 Repo State (2026-09-14)

| Field | Value |
|-------|-------|
| Branch | main |
| Last commit | `00f81bc` — chore: update NeuralMind team memory snapshot [skip ci] (2026-09-13) |
| Uncommitted | 14 files (bm25, core, embedder, context_selector, document_ingestion, graphgen, turbovec_backend, test fixtures, peptide benchmark) |
| Ahead/Behind | 0/0 (in sync) |
| Stale days | 1 day since last commit |

---

*NeuralMind v3.10.0 — P0 retrieval performance fix in progress. ROOT CAUSE: vector-BM25 ID mismatch. Safety protocol in ADR. Uncommitted work needs commit or revert after T1-T3 verification.*
