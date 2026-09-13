# NeuralMind — Kanban Board (CANONICAL — `dfrostar/neuralmind`)

**Last updated:** 2026-09-13 (verified against git status)
**Repo:** `neuralmind` (dfrostar/neuralmind)
**Version:** 3.4.1
**Branch:** release-please--branches--main
**Status:** ✅ MERGED TO MAIN (release branch)

> **⚠️ DUPLICATES:** `neuralmind-fresh/KANBAN.md` points here. Do NOT edit those copies — edit this file only.

---

## ✅ COMPLETE: All Issues (2026-08-11 → 2026-09-02)

| Category | Count | Status |
|----------|-------|--------|
| P0 Fixes | 3 | ✅ Merged |
| P1 Fixes | 2 | ✅ Merged |
| Gap Closure | 3 | ✅ Merged |
| P2 Fixes | 5 | ✅ Merged |
| P3 Fixes | 2 | ✅ Merged |
| Code/Doc Scoring | 4 | ✅ Merged |
| QA Fixes | 11 | ✅ Merged |
| **Total** | **30** | **✅ Merged** |

## ✅ v3.1.4 — Shipped

- Future-proofing tests + cross-project validation
- Release notes, CLI ref, use cases, SEO propagated
- SBOM published to site

## ✅ v3.4.1 — Shipped

- N-13 synapse seeding tightened to prevent false positive explosion
- Tiktoken bumped to 0.14.0
- Ruff bumped to 0.16.4
- Compliance docs updated

---

## 📋 IN PROGRESS (Staged/Uncommitted in `neuralmind`)

|| ID | Task | Status | Files |
||----|------|--------|-------|
|| U-01 | BGE embedder integration | 🔄 Staged | `neuralmind/bge_embedder.py`, `tests/test_bge_embedder.py` |
|| U-02 | New use cases | 🔄 Staged | 4 docs in `docs/use-cases/` |
|| U-03 | Synapse Module wiki | 🔄 Staged | `docs/wiki/Synapse-Module.md` |
|| — | Test fixture updates | 🔄 Modified | 8 fixture extraction caches |

> **Note:** U-04 (CI regression floor fix) was committed as `587c09b` on 2026-09-04.
> **⚠️ Behind origin by ~40 commits.** Pull/rebase required to sync with latest main (v3.10.0 on origin).

---

## 📋 ACTIVE BACKLOG

| ID | Issue | Priority | Track |
|----|-------|----------|-------|
| U-01 | Logos training transformers incompatibility | P1 | Training |
| U-02 | Corpus expansion (all manuscripts) | P2 | Training |
| U-03 | Post-training perplexity evaluation | P2 | Training |
| U-04 | Resume from checkpoint | P2 | Training |
| U-05 | Pull/rebase origin (20 commits behind) | P1 | Infra |

---

## 📚 KEY DOCS

| Doc | Location |
|-----|----------|
| Code/Doc Scoring TRD | `neuralmind-autopilot/docs/specs/CODE-DOC-SCORING-TRD.md` |
| Training SOP | `bible-llm/docs/TRAINING-SOP.md` |
| Machine specs | See Training SOP §1 |

---

## 📊 Repo State (2026-09-12)

| Field | Value |
|-------|-------|
| Branch | release-please--branches--main |
| Last commit | `587c09b` — fix(ci): lower regression test floor to 3.0× (2026-09-04) |
| Staged | KANBAN.md, bge_embedder.py + test, 4 use-case docs, Synapse-Module wiki |
| Modified | 8 fixture extraction_cache.json files |
| Stale days | 8 days since last commit |
| ⚠️ Behind origin by ~40 commits — pull/rebase required (origin has v3.10.0) |

---

*NeuralMind v3.4.1 — all dogfood issues resolved. Uncommitted work: BGE embedder + use cases + Synapse Module wiki.*