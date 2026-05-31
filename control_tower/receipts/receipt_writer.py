"""
Agent Control Tower - Receipt Writer (Step 3.1)

Takes OperatorDecision + originating context and produces auditable receipts
with basic content hashing (CTGH-inspired).

Per the map (MVP_END_TO_END_ROADMAP.md Phase 3):
- Structured receipt
- Includes original event, decision, rationale, etc.
- Basic content hashing
- Stored in dedicated location
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..models import OperatorDecision


@dataclass
class Receipt:
    """Structured, auditable receipt for a single operator decision."""
    receipt_id: str
    timestamp: str
    request_id: str
    event_id: str
    run_id: str
    action_type: str
    target: str
    summary: str
    decision: str
    rationale: str
    corrected_action: Optional[str]
    content_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


class ReceiptWriter:
    """
    Builds and persists receipts from OperatorDecision + context.

    Usage:
        writer = ReceiptWriter()
        receipt = writer.create_receipt(decision, context_dict)
        writer.write_receipt(receipt, output_dir)
    """

    def __init__(self):
        pass

    def _compute_content_hash(self, receipt_data: Dict[str, Any]) -> str:
        """Simple CTGH-inspired content hash of the core decision payload."""
        # Sort keys for deterministic hashing
        canonical = json.dumps(receipt_data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def create_receipt(
        self,
        decision: OperatorDecision,
        context: Dict[str, Any],
    ) -> Receipt:
        """
        Create a Receipt from an OperatorDecision and its originating context.

        Context should contain at minimum:
            - request_id
            - event_id (from original AgentEvent)
            - run_id
            - action_type
            - target
            - summary
        """
        now = datetime.now(timezone.utc).isoformat()

        receipt_data_for_hash = {
            "request_id": decision.request_id,
            "decision": decision.decision,
            "rationale": decision.rationale,
            "corrected_action": decision.corrected_action,
            "timestamp": decision.timestamp,
            **{k: context.get(k) for k in ["event_id", "run_id", "action_type", "target", "summary"]},
        }

        content_hash = self._compute_content_hash(receipt_data_for_hash)

        receipt_id = f"RCPT-{content_hash[:12]}"

        return Receipt(
            receipt_id=receipt_id,
            timestamp=now,
            request_id=decision.request_id,
            event_id=context.get("event_id", ""),
            run_id=context.get("run_id", ""),
            action_type=context.get("action_type", ""),
            target=context.get("target", ""),
            summary=context.get("summary", ""),
            decision=decision.decision,
            rationale=decision.rationale,
            corrected_action=decision.corrected_action,
            content_hash=content_hash,
        )

    def write_receipt(self, receipt: Receipt, output_dir: Path) -> Path:
        """Write a single receipt as JSON to the given directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{receipt.receipt_id}.json"
        filepath.write_text(receipt.to_json(), encoding="utf-8")
        return filepath

    def write_receipts_batch(
        self,
        decisions: list[OperatorDecision],
        contexts: Dict[str, Dict[str, Any]],  # keyed by request_id
        output_dir: Path,
    ) -> list[Path]:
        """Write multiple receipts in one batch and update the linkage manifest."""
        written = []
        manifest_entries = []
        for decision in decisions:
            ctx = contexts.get(decision.request_id, {})
            receipt = self.create_receipt(decision, ctx)
            path = self.write_receipt(receipt, output_dir)
            written.append(path)

            # Build manifest entry for explicit linking back to original event
            manifest_entries.append({
                "event_id": receipt.event_id,
                "request_id": receipt.request_id,
                "receipt_id": receipt.receipt_id,
                "decision": receipt.decision,
                "timestamp": receipt.timestamp,
            })

        if manifest_entries:
            self._append_to_manifest(manifest_entries, output_dir)

        return written

    def _append_to_manifest(self, entries: list[Dict[str, Any]], output_dir: Path) -> None:
        """Maintain a simple queryable manifest that links event_id → receipts."""
        manifest_path = output_dir / "receipts_manifest.jsonl"
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "a", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    @staticmethod
    def load_manifest(output_dir: Path) -> list[Dict[str, Any]]:
        """Load the linkage manifest. Allows querying which receipts belong to which original events."""
        manifest_path = output_dir / "receipts_manifest.jsonl"
        if not manifest_path.exists():
            return []
        entries = []
        for line in manifest_path.read_text(encoding="utf-8").strip().splitlines():
            if line:
                entries.append(json.loads(line))
        return entries

    @staticmethod
    def find_receipts_for_event(event_id: str, output_dir: Path) -> list[Dict[str, Any]]:
        """Query the manifest for all receipts linked to a specific original event_id."""
        return [e for e in ReceiptWriter.load_manifest(output_dir) if e.get("event_id") == event_id]
