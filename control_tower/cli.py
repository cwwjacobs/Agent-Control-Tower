"""
Agent Control Tower - Main CLI Entrypoint (Phase 5)

This provides the `control-tower` / `python -m control_tower` interface.

Commands wired so far (more will be added as we push through Phase 5):
- export-training
- generate-receipts
- run-gate

You told us to go, my love. We are building the actual usable tool for you.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import the real workers we already built
from .orchestrator import ControlTower
from .training.training_exporter import TrainingExporter
from .receipts.receipt_writer import ReceiptWriter
from .gate import run_cli_gate
from .interfaces.decision_handler import DecisionHandler  # available for future handlers
from .demo.export_training_data import main as export_training_main
from .demo.generate_receipts_from_gate import main as generate_receipts_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="control-tower",
        description="Agent Control Tower — local supervision, receipts, and training data for solo operators.",
        epilog="Made with love and discipline for the Responsible Operator."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # export-training
    p_train = subparsers.add_parser(
        "export-training",
        help="Export training data from existing Gate decisions + receipts."
    )
    p_train.add_argument(
        "--output",
        type=Path,
        default=Path("current_run/training_data.jsonl"),
        help="Where to write the training JSONL (default: current_run/training_data.jsonl)"
    )
    p_train.set_defaults(func=cmd_export_training)

    # generate-receipts
    p_receipts = subparsers.add_parser(
        "generate-receipts",
        help="Generate receipts from existing operator decisions."
    )
    p_receipts.add_argument(
        "--output-dir",
        type=Path,
        default=Path("current_run/receipts"),
        help="Directory to write receipts into (default: current_run/receipts)"
    )
    p_receipts.set_defaults(func=cmd_generate_receipts)

    # run-gate (interactive)
    p_gate = subparsers.add_parser(
        "run-gate",
        help="Launch the interactive Gate on DecisionRequests from a file."
    )
    p_gate.add_argument(
        "--input",
        type=Path,
        default=Path("current_run/escalated_decisions.jsonl"),
        help="JSONL file of DecisionRequests (default: current_run/escalated_decisions.jsonl)"
    )
    p_gate.add_argument(
        "--save-decisions",
        type=Path,
        default=Path("current_run/operator_decisions.jsonl"),
        help="Where to save the OperatorDecision records (default: current_run/operator_decisions.jsonl)"
    )
    p_gate.set_defaults(func=cmd_run_gate)

    return parser


def cmd_export_training(args: argparse.Namespace) -> None:
    print("[control-tower] Exporting training data...")
    export_training_main()  # reuses the existing demo logic for now
    print(f"[control-tower] Training data written (see current_run/training_data.jsonl)")


def cmd_generate_receipts(args: argparse.Namespace) -> None:
    print(f"[control-tower] Generating receipts into {args.output_dir}...")
    # For now reuse the demo; later we can make it fully non-demo
    generate_receipts_main()
    print(f"[control-tower] Receipts generated.")


def cmd_run_gate(args: argparse.Namespace) -> None:
    print(f"[control-tower] Launching interactive Gate on {args.input}...")
    from .demo.run_gate_on_samples import load_decision_requests
    from .gate import Gate

    requests = load_decision_requests(args.input)

    if not requests:
        print("[control-tower] No DecisionRequests found.")
        return

    # Correct pattern per the Operator's guidance:
    # Create the engine first, then supply the interface (handler) at integration time.
    # This is "engine then interfaces".
    tower = ControlTower(Path("."), default_handler=Gate())
    # For now we still use the convenience for the interactive loop,
    # but the engine is ready to accept any DecisionHandler (TUI, etc.).
    decisions = run_cli_gate(requests, auto_save_path=args.save_decisions)
    print(f"[control-tower] Gate session complete. Decisions saved to {args.save_decisions}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
