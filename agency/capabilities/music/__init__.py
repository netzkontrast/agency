"""music — clustered domain capability (Spec 093 master / Spec 094 lifecycle child).

Music is the reference clustered domain capability: album conceptualization plus one representative verb per cluster (text, audio/mastering, catalogue DB, content/promo, state, cloud), each reaching external work through an injected Spec-002 Driver and recording provenance — so a release audit is one graph traversal.

Use when: conceptualizing or producing an album — turning an idea into a gated concept, mastering to a target loudness, drafting promo copy, or auditing a release — as the reference for how a first-class clustered domain capability extends agency.
Triggers:
- An album idea that needs a structured, gated concept before production
- A music production step (master, promo, lyric analysis) that should be recorded as provenance
- A reference for how a clustered domain capability reaches external tools via Drivers
Red flags:
- Shelling out to ffmpeg/Postgres/R2 directly → route through a Spec-002 Driver via ctx.get_driver
- Producing a document without an artefact → set data['artefact'] so the Registry records PRODUCES
"""
from ._main import MusicCapability

__all__ = ["MusicCapability"]
