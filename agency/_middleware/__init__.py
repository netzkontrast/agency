"""Engine middleware — cross-cutting helpers that are NOT capabilities.

The canon (CORE.md:16-18) names loop-detection *middleware*, not a concept: it
is a fast-twitch self-interrupt signal an engine/hooks layer can run, never a
discoverable verb. Modules here are imported by the engine or a future hooks
layer; they are never registered via `search`/`get_schema`/`execute`.
"""
