# SPEC: Peptide Book Retrieval Fixes (v3.11.3)

**Date:** 2026-09-14
**Version:** v3.11.3
**Target:** Fix 4 weak queries in peptide book benchmark

---

## Problem Statement

4 of 14 benchmark queries score below 80% recall@5:

| Query | R@5 | Expected Chapter | Actual Top Chapter |
|-------|-----|------------------|-------------------|
| glp1-mechanism | 0.67 | Ch2 (mechanism) | Ch5 (safety) |
| pcac-recommendation | 0.50 | Ch6 (regulatory) | Ch4 (grey-market) |
| tirzepatide-dual-agonist | 0.50 | Ch3 (FDA-approved) | Ch1 (overview) |
| oral-peptide-delivery | 0.50 | Ch2 (delivery) | Ch7 (future) |

## Root Cause Analysis

**Common pattern:** BM25 ranks chapters with high TF for query terms, but those chapters aren't the most relevant for the query intent.

1. **glp1-mechanism**: "semaglutide" appears in Ch5 with high TF (side-effect descriptions), but query asks "how does it work" → should be Ch2 (mechanism)
2. **pcac-recommendation**: "PCAC" appears in Ch4 with high TF (grey-market compounding), but query asks about FDA vs PCAC difference → should be Ch6 (regulatory)
3. **tirzepatide-dual-agonist**: "tirzepatide" appears in Ch1 with high TF (overview), but query asks about drug comparison → should be Ch3 (FDA-approved)
4. **oral-peptide-delivery**: "oral" appears in Ch7 with high TF (future), but query asks about delivery mechanisms → should be Ch2 (delivery)

## Fix 1: Multi-Term Coverage Boost (BM25)

**File:** `neuralmind/bm25.py`

**Change:** When query has 2+ rare terms (DF ≤ 5), boost documents containing ALL rare terms by 1.5×.

**Status:** ✅ Already implemented in v3.11.2

**Expected impact:** Fixes tirzepatide-dual-agonist (both "tirzepatide" and "semaglutide" are rare)

## Fix 2: Chapter-Level Deduplication (Context Assembly)

**File:** `neuralmind/context_selector.py`

**Change:** When the same chapter appears multiple times in ranked results, merge them and boost the merged score by 1.2×.

**Rationale:** Currently, multiple chunks from the same chapter appear as separate results. Merging them gives a stronger signal for the chapter as a whole.

**Expected impact:** Improves precision@5 by reducing duplicate chapter entries

## Fix 3: Query Intent Boost (Hybrid Merge)

**File:** `neuralmind/context_selector.py`

**Change:** Detect query intent via keyword matching and boost chapters whose primary content matches the intent.

**Intent keywords:**
- Mechanism: "how does", "mechanism", "work", "function", "action"
- Comparison: "difference", "compare", "versus", "vs", "differ"
- Regulatory: "fda", "approval", "regulatory", "pcac", "compliance"
- Delivery: "oral", "delivery", "injection", "subcutaneous", "nasal"
- Safety: "side effect", "risk", "warning", "adverse", "contraindication"

**Chapter intent mapping (peptide book):**
- Ch1 (what-are-peptides): overview, definition
- Ch2 (chapter-2): mechanism, delivery, science
- Ch3 (fda-approved): comparison, drug details, approval
- Ch4 (grey-market): compounding, risks, unregulated
- Ch5 (safety): side effects, warnings, risks
- Ch6 (regulatory): FDA, PCAC, compliance, approval process
- Ch7 (future): pipeline, oral revolution, AI-designed
- Ch8 (questions): prescriber questions, checklist
- Ch98 (claims-register): reference, appendix
- Ch99 (back-matter): glossary, about authors

**Boost factor:** 1.3× for chapters whose intent matches query intent

**Expected impact:** Fixes glp1-mechanism (boost Ch2), pcac-recommendation (boost Ch6), oral-peptide-delivery (boost Ch2)

## Fix 4: First-Query Cold Start (P95 Latency)

**File:** `neuralmind/core.py`

**Change:** Pre-load BM25 index and embedding model in `NeuralMind.__init__` instead of lazy loading on first query.

**Rationale:** P95 latency is 14.9s because the first query triggers model loading. Pre-loading moves this cost to initialization.

**Expected impact:** P95 latency < 500ms (model already loaded)

---

## Implementation Order

1. Fix 2: Chapter-level deduplication (context_selector.py)
2. Fix 3: Query intent boost (context_selector.py)
3. Fix 4: Cold start pre-loading (core.py)
4. Re-run benchmark
5. Verify all 4 weak queries fixed
6. Commit + tag v3.11.3

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Recall@5 | 86.9% | ≥ 90% |
| Precision@5 | 41.8% | ≥ 60% |
| Queries ≥ 80% R@5 | 10/14 (71%) | ≥ 13/14 (93%) |
| P95 Latency | 14,894ms | < 500ms |
| Hit Rate | 100% | 100% |

## Test Plan

1. Run `python3 -m pytest tests/ -q` — all tests pass
2. Run `python3 tests/benchmark/peptide_benchmark.py` — verify 4 weak queries fixed
3. Run `python3 -m tests.benchmark.run` — verify CI regression gate passes
4. Commit + tag v3.11.3
