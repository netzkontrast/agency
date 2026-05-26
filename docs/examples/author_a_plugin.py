#!/usr/bin/env python
"""Example: author a tiny Claude Code plugin with the agency engine.

Walks the `plugin-dev` skill one phase at a time (progressive disclosure). Each
step emits a prestructured document (manifest -> skill -> command -> marketplace
entry) and ends at a hard confirm gate. Every step is recorded as provenance.

Run from the repo root:

    python docs/examples/author_a_plugin.py
"""
import json
import tempfile

from agency.capabilities.plugin import scaffold
from agency.engine import Engine
from agency.skill import SkillRun


def main() -> None:
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture("author a demo plugin", "an installable plugin", "manifest valid")
    e.intent.confirm(iid)

    run = SkillRun(e.memory, iid, e.ontology.skill("plugin-dev"), registry=e.registry)
    steps = [
        {"name": "demo", "version": "0.1.0", "description": "A demo plugin"},
        {"name": "greet", "description": "Use when you greet the user", "body": "# Greet\nSay hello."},
        {"name": "go", "description": "Use when you run the demo", "body": "Run it."},
        {"name": "demo", "version": "0.1.0", "description": "A demo plugin", "source": "netzkontrast/agency"},
    ]
    for outputs in steps:
        phase = run.current()["name"]
        status = run.submit(outputs)["status"]
        print(f"phase {phase:<12} -> {status}")

    print(f"phase {run.current()['name']:<12} -> hard gate")
    print("confirm        ->", run.submit({"user_confirmed": "yes"}, confirmed=True)["status"])

    print("\nartefacts produced (each a prestructured step document):")
    for a in e.memory.provenance(iid)["artefacts"]:
        print("  -", a["kind"])

    print("\nthe manifest the engine generated:")
    print(scaffold("demo", "0.1.0", "A demo plugin")["result"])

    e.memory.close()


if __name__ == "__main__":
    main()
