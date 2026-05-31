# `.luminary/` Ledger

This directory is the local evidence spine for a project.

- `events/events.jsonl`: append-only event ledger.
- `claims/claims.jsonl`: claim ledger with support status and boundaries.
- `receipts/`: generated run receipts.
- `maps/trace_evidence_map.json`: convenience map from trace id to event ids.

Do not treat this as production observability. Treat it as a compact, inspectable archive for trace hardening.
