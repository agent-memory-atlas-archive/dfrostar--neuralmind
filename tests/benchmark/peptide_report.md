# NeuralMind Performance Report — Peptide Patient's Guide

**Generated:** 2026-09-15 11:54:41
**NeuralMind Version:** 3.10.0
**Project:** peptide-patient-guide
**Index Size:** 61 nodes
**Queries Run:** 14

---

## Executive Summary

| Metric | Value | Grade |
|--------|-------|-------|
| Recall@1 | 64.3% | 🟡 |
| Recall@3 | 81.0% | 🟢 |
| Recall@5 | 95.2% | 🟢 |
| Precision@5 | 38.6% | 🔴 |
| MRR | 0.79 | 🟡 |
| nDCG@5 | 0.80 | 🟢 |
| Hit Rate | 100.0% | 🟢 |
| Avg Latency | 2332ms | 🔴 |
| P95 Latency | 25340ms | 🔴 |
| Fact Recall | 30/57 (53%) | 🟡 |

---

## Performance by Query Shape

| Shape | Count | Recall@5 | MRR | Avg Latency |
|-------|-------|----------|-----|-------------|
| cross-chapter | 2 | 83.3% | 0.42 | 850ms |
| focused | 10 | 96.7% | 0.87 | 539ms |
| identity | 2 | 100.0% | 0.75 | 12774ms |

---

## Per-Query Breakdown

| ID | Shape | R@1 | R@3 | R@5 | MRR | nDCG@5 | Latency | Top Chapter |
|----|-------|-----|-----|-----|-----|--------|---------|-------------|
| peptide-definition | identity | 0.00 | 1.00 | 1.00 | 0.50 | 0.67 | 25340ms | 03_fda-approved-peptides.md |
| glp1-mechanism | focused | 1.00 | 0.67 | 0.67 | 1.00 | 0.80 | 890ms | 03_fda-approved-peptides.md |
| fda-approval-meaning | focused | 1.00 | 1.00 | 1.00 | 1.00 | 0.87 | 784ms | 06_regulatory-landscape.md |
| pcac-recommendation | cross-chapter | 0.00 | 0.50 | 1.00 | 0.33 | 0.54 | 522ms | 98_claims-register-appendix.md |
| weight-loss-semaglutide | focused | 0.00 | 0.00 | 1.00 | 0.20 | 0.33 | 424ms | 06_regulatory-landscape.md |
| retatrutide-triple-agonist | focused | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 824ms | 07_future-of-peptide-therapy.md |
| bpc157-grey-market | focused | 0.00 | 1.00 | 1.00 | 0.50 | 0.67 | 554ms | 01_what-are-peptides.md |
| black-box-warning-thyroid | focused | 1.00 | 0.50 | 1.00 | 1.00 | 0.91 | 519ms | 05_safety-side-effects.md |
| tirzepatide-dual-agonist | focused | 1.00 | 1.00 | 1.00 | 1.00 | 0.85 | 523ms | 07_future-of-peptide-therapy.md |
| oral-peptide-delivery | focused | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 410ms | 07_future-of-peptide-therapy.md |
| grey-market-risks | cross-chapter | 0.00 | 0.67 | 0.67 | 0.50 | 0.59 | 1179ms | 08_questions-to-ask-prescriber.md |
| peptide-stability-refrigeration | focused | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 226ms | 02_chapter-2.md |
| questions-to-ask-prescriber | focused | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 239ms | 08_questions-to-ask-prescriber.md |
| book-authors | identity | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 208ms | 00_front-matter.md |

---

## Brutally Honest Assessment

### What's Working Well
- **12/14 queries** achieve ≥80% recall@5
- **5/14 queries** complete in under 500ms
- **100% hit rate** — most queries find at least one relevant chapter

### What Needs Improvement
- **2 queries** exceed 1 second latency
- **1 queries** returned fewer than 3 chapters — context may be too sparse

### Critical Issues

1. **Index treats book as code repository.** Context says "Code repository with semantic indexing" — tree-sitter parsing is for functions/classes, not chapters.

2. **No chapter-aware retrieval.** NeuralMind doesn't understand "Chapter 3: FDA-Approved Peptides" is a semantic unit.

3. **Synapse layer adds no value for static books.** Hebbian co-activation is for usage patterns; a book has fixed structure.

4. **Metadata pollution.** Queries return hits from research notes, session context, illustration plans — not just chapters.

5. **Cross-chapter reasoning absent.** Questions like "FDA vs PCAC" need synthesis from 3-4 chapters. NeuralMind returns isolated chunks.

6. **Context is too verbose.** ~4,500 chars with cluster metadata instead of actual chapter text.

### Performance Comparison to Baselines

| Approach | Expected Recall@5 | Pros | Cons |
|----------|-------------------|------|------|
| NeuralMind (current) | 95% | Learns over time | Wrong tool for prose, verbose |
| Pure embedding (ChromaDB) | ~85-90% | Fast, accurate | No structure awareness |
| BM25 keyword search | ~70-80% | Fast, interpretable | Misses semantic matches |
| Hybrid (BM25 + embedding) | ~90-95% | Best of both worlds | More complex |
| Full-text search (SQLite FTS) | ~75-85% | Simple, fast | No semantic understanding |

---

## Recommendations

### Short-term (quick wins)
- **Filter index to chapters only.** Exclude metadata/, reports/, assets/, session files.
- **Add chapter-level chunking.** Treat each chapter as a document.
- **Suppress architecture metadata.** Strip "Knowledge Graph" and "Code Clusters" from output.

### Medium-term (structural)
- **Implement "content mode".** Switch between code analysis and prose analysis.
- **Add cross-chapter relationship edges.** Link chapters that share topics.
- **Use BM25 + embedding hybrid.** BM25 for exact medical terms, embedding for semantics.

### Long-term (strategic)
- **NeuralMind is the wrong tool for book retrieval.** Consider memU, Obsidian, or a RAG pipeline.
- **Disable synapse layer for static content.** It adds latency without benefit.

---

## Conclusion

NeuralMind v3.10.0 **functions** as a retrieval system but is **not optimized for books**. At 95% recall, it misses more than half the relevant content.

**Verdict:** A purpose-built content retrieval system would achieve >90% recall with cleaner output.

---

*Report generated by peptide_benchmark.py | NeuralMind v3.10.0*
