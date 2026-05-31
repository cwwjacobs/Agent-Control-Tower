"""
Agent Control Tower - Watcher Module

Responsible for watching live agent activity (events.jsonl and hook payloads)
and feeding them into the pipeline in real time.

This is the entry point of the "spine".
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterator, Callable, Optional

from ..parser import AgentEvent, parse_event


class LiveWatcher:
    """
    Watches a .luminary directory for new events and yields them.
    """

    def __init__(self, project_root: Path, poll_interval: float = 0.5):
        self.project_root = project_root.resolve()
        self.events_file = self.project_root / ".luminary" / "events" / "events.jsonl"
        self.poll_interval = poll_interval
        self._last_position = 0

    def watch(self) -> Iterator[AgentEvent]:
        """
        Generator that yields new AgentEvents as they appear.
        This is a simple polling implementation for the MVP.
        """
        while True:
            if not self.events_file.exists():
                time.sleep(self.poll_interval)
                continue

            try:
                with open(self.events_file, "r", encoding="utf-8") as f:
                    f.seek(self._last_position)
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            raw_event = json.loads(line)
                            event = parse_event(raw_event)
                            yield event
                        except json.JSONDecodeError:
                            continue
                    self._last_position = f.tell()
            except FileNotFoundError:
                pass

            time.sleep(self.poll_interval)

    def watch_once(self, limit: Optional[int] = None) -> list[AgentEvent]:
        """One-shot read of all current events (useful for testing)."""
        events = []
        if not self.events_file.exists():
            return events

        with open(self.events_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if limit is not None and i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    raw_event = json.loads(line)
                    events.append(parse_event(raw_event))
                except json.JSONDecodeError:
                    continue
        return events
