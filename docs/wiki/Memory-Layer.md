# Memory Layer

The Memory Layer gives agents persistent, queryable decision memory: every architectural decision is recorded with its rationale, evidence, and the git commit where it was made — and is automatically invalidated when the code it describes changes.

## Overview

- **Storage:** SQLite (`.neuralmind/memory.db` in your project root), created on first use
- **Search:** FTS5 full-text search over titles, rationales, and evidence
- **Invalidation:** file-touch, commit mismatch, and cascade rules — decisions referencing changed files go stale automatically
- **Access:** CLI (`neuralmind memory`), MCP tools (4 new), and Python API

## CLI Reference

### Record a decision

```bash
neuralmind memory record [project_path] --title "TITLE" [--rationale TEXT]
    [--commit SHA] [--files "a.py,b.py"] [--type architecture]
    [--rejected '{"option":"X","reason":"..."}']
    [--evidence '{"type":"supporting","content":"...","source":"..."}']
    [--confidence 0.95]
```

### Query decisions

```bash
neuralmind memory query [project_path] "natural language query" [--limit 10] [--status active]
```

### Audit

```bash
neuralmind memory audit [project_path] [--stale-only] [--orphaned-only] [--format md|json]
```

Age-based staleness (STALE_DAYS=90) plus orphaned-SHA detection (commit no longer in history).

### Amend / Invalidate / Restore

```bash
neuralmind memory amend <decision-id> [--rationale TEXT] [--evidence JSON] [--rejected JSON]
neuralmind memory invalidate <decision-id> --reason "why"
neuralmind memory restore <decision-id>
```

### Export

```bash
neuralmind memory export [project_path] [--format md|json] [--output FILE]
```

### Eval harness

```bash
neuralmind memory eval [project_path]
```

## MCP Tools

Registered in the MCP server (25 tools total as of v4.1.0):

| Tool | Arguments | Description |
|------|-----------|-------------|
| `neuralmind_query_decisions` | `project_path`, `query`, `limit` | Natural-language search over decisions |
| `neuralmind_audit_decisions` | `project_path`, `stale_only` | List decisions, filter by status |
| `neuralmind_record_decision` | `project_path`, `title`, `rationale`, `commit`, `files_affected`, `decision_type`, `confidence`, `evidence`, `rejected_alternatives` | Store a new decision |
| `neuralmind_invalidate_decision` | `project_path`, `decision_id`, `reason` | Mark a decision stale |

### RBAC

- **Builder role:** all 4 memory tools
- **Reader role:** `query` + `audit` only — write tools verified denied

## Invalidation Semantics

- `invalidate()` sets status to `INVALIDATED` (not `STALE`) and appends the reason to the decision's evidence
- Invalidation is **file-scoped**: a commit mismatch only invalidates decisions whose `files_affected` include the changed files — untouched decisions stay active even on commit mismatch
- Audit returns a list; STALE detection is age-based (90 days) plus orphaned-SHA detection
- `DecisionStore` has no `.close()` — connections are managed internally

## Python API

```python
from neuralmind.memory.store import DecisionStore

store = DecisionStore(project_path=".")
store.record(
    title="Use SQLite for decision store",
    rationale="Single-file, no server, ACID-compliant",
    files_affected=["neuralmind/memory/store.py"],
    decision_type="architecture",
    confidence=0.95,
)
results = store.query("database choice")
```

## Testing

60 tests in `tests/memory/` cover store CRUD/FTS/audit/export, invalidation engine (file-touch, commit mismatch, cascade, idempotency), MCP tool dispatch, eval harness, and integration (lifecycle, export/import roundtrip, 10-thread concurrency, broken-git graceful degradation). All stdlib-only.
