# Luminary I/O Archivist Agent Contract

When working in this repository, treat Luminary I/O Archivist as the evidence ledger.

Project root:
`~/Desktop/SWARMPRIMETRACE`

Before meaningful work:
1. Use or create a `LUMINARY_RUN_ID`.
2. Log the user instruction or session activation.
3. For every meaningful file read, file edit, command run, validation, decision, trace update, or generated artifact, log an event with:
   `python3 scripts/luminary_log_event.py`

For Grok/Grok Build:
- Prefer launching through `integrations/grok/lumi-grok` or `scripts/luminary_agent_run.sh grok -- grok-build`.
- If running directly, call `scripts/luminary_log_artifact.sh` for any generated output file.
- At the end of a run, call `scripts/luminary_session_receipt.sh`.

Claim boundary:
The ledger proves logged events and receipts. It does not prove universal correctness or that uncaptured actions did not occur.
