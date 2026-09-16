# NeuralMind Performance Report — Peptide Patient's Guide

**Generated:** 2026-09-15 20:32:27
**NeuralMind Version:** 3.10.0
**Project:** peptide-patient-guide
**Index Size:** 61 nodes
**Queries Run:** 14

---

## Executive Summary

| Metric | Value | Grade |
|--------|-------|-------|
| Recall@1 | 78.6% | 🟢 |
| Recall@3 | 73.8% | 🟡 |
| Recall@5 | 86.9% | 🟡 |
| Precision@5 | 37.3% | 🔴 |
| MRR | 0.83 | 🟢 |
| nDCG@5 | 0.79 | 🟡 |
| Hit Rate | 92.9% | 🟢 |
| Avg Latency | 921ms | 🟡 |
| P95 Latency | 7616ms | 🔴 |
| Fact Recall | 48/57 (84%) | 🟢 |

---

## Performance by Query Shape

| Shape | Count | Recall@5 | MRR | Avg Latency |
|-------|-------|----------|-----|-------------|
| cross-chapter | 2 | 83.3% | 1.00 | 307ms |
| focused | 10 | 85.0% | 0.76 | 444ms |
| identity | 2 | 100.0% | 1.00 | 3921ms |

---

## Per-Query Breakdown

| ID | Shape | R@1 | R@3 | R@5 | MRR | nDCG@5 | Latency | Top Chapter |
|----|-------|-----|-----|-----|-----|--------|---------|-------------|
| peptide-definition | identity | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 7616ms | 01_what-are-peptides.md |
| glp1-mechanism | focused | 1.00 | 0.67 | 1.00 | 1.00 | 0.90 | 181ms | 02_chapter-2.md |
| fda-approval-meaning | focused | 1.00 | 1.00 | 1.00 | 1.00 | 0.81 | 230ms | 06_regulatory-landscape.md |
| pcac-recommendation | cross-chapter | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 209ms | 04_grey-market-compounds.md |
| weight-loss-semaglutide | focused | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 168ms | 02_chapter-2.md |
| retatrutide-triple-agonist | focused | 0.00 | 0.50 | 1.00 | 0.33 | 0.54 | 303ms | 01_what-are-peptides.md |
| bpc157-grey-market | focused | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 390ms | 04_grey-market-compounds.md |
| black-box-warning-thyroid | focused | 1.00 | 1.00 | 1.00 | 1.00 | 0.94 | 445ms | 05_safety-side-effects.md |
| tirzepatide-dual-agonist | focused | 0.00 | 0.00 | 0.50 | 0.25 | 0.31 | 824ms | 01_what-are-peptides.md |
| oral-peptide-delivery | focused | 1.00 | 1.00 | 1.00 | 1.00 | 0.94 | 387ms | 07_future-of-peptide-therapy.md |
| grey-market-risks | cross-chapter | 1.00 | 0.67 | 0.67 | 1.00 | 0.73 | 405ms | 06_regulatory-landscape.md |
| peptide-stability-refrigeration | focused | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 754ms | 02_chapter-2.md |
| questions-to-ask-prescriber | focused | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 760ms | 08_questions-to-ask-prescriber.md |
| book-authors | identity | 1.00 | 0.50 | 1.00 | 1.00 | 0.84 | 227ms | 00_front-matter.md |

---

## Brutally Honest Assessment

### What's Working Well
- **11/14 queries** achieve ≥80% recall@5
- **10/14 queries** complete in under 500ms
- **93% hit rate** — most queries find at least one relevant chapter

### What Needs Improvement
- **1 queries** returned ZERO relevant chapters: weight-loss-semaglutide
- **1 queries** have <50% recall@5
- **1 queries** exceed 1 second latency

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
| NeuralMind (current) | 87% | Learns over time | Wrong tool for prose, verbose |
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

NeuralMind v3.10.0 **functions** as a retrieval system but is **not optimized for books**. At 87% recall, it misses more than half the relevant content.

**Verdict:** A purpose-built content retrieval system would achieve >90% recall with cleaner output.

---

*Report generated by peptide_benchmark.py | NeuralMind v3.10.0*
