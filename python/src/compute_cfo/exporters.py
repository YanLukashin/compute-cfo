"""Cost event exporters."""

from __future__ import annotations

import json
import sys
import urllib.request
from typing import Callable

from .types import CostEvent

Exporter = Callable[[CostEvent], None]


def console_exporter(event: CostEvent) -> None:
    """Print cost event to stderr."""
    cost_str = f"${event.cost_usd:.6f}" if event.cost_usd is not None else "$?.??????"
    total_tokens = event.input_tokens + event.output_tokens

    parts = [
        f"\033[90m[compute-cfo]\033[0m",
        f"\033[1m{event.model}\033[0m",
        f"{total_tokens} tokens",
        f"\033[33m{cost_str}\033[0m",
    ]

    if event.tags:
        tag_str = " ".join(f"{k}:{v}" for k, v in event.tags.items())
        parts.append(f"\033[90m{tag_str}\033[0m")

    print(" | ".join(parts), file=sys.stderr)


def jsonl_exporter(path: str = "compute_cfo_events.jsonl") -> Exporter:
    """Return an exporter that appends JSON lines to a file."""

    def _export(event: CostEvent) -> None:
        with open(path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    return _export


def webhook_exporter(url: str) -> Exporter:
    """Return an exporter that POSTs cost events to a URL."""

    def _export(event: CostEvent) -> None:
        data = json.dumps(event.to_dict()).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # fire-and-forget

    return _export


def get_exporter(spec: str) -> Exporter:
    """Parse an exporter specification string and return the exporter.

    Supported formats:
        "console" — print to stderr
        "jsonl" — write to compute_cfo_events.jsonl
        "jsonl:/path/to/file.jsonl" — write to custom path
        "webhook:https://example.com/hook" — POST to URL
    """
    if spec == "console":
        return console_exporter

    if spec == "jsonl":
        return jsonl_exporter()

    if spec.startswith("jsonl:"):
        return jsonl_exporter(spec[6:])

    if spec.startswith("webhook:"):
        return webhook_exporter(spec[8:])

    raise ValueError(
        f"Unknown exporter: {spec!r}. "
        f"Use 'console', 'jsonl', 'jsonl:/path', or 'webhook:URL'."
    )
