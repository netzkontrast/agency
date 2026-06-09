<!-- agency-generated: v1 -->
# music.check_name_exposure

Scan text for forbidden roster names (driver-free, deterministic) (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text, roster (defaults to config blocklist).` |  |  |

## Returns

``{hits: [{name, count}], count, roster_size}``.

## Chain-next

``music.name_exposure_gate`` to block on a hit.

## Details

Spec 119 — F6 from Spec 117. A personal/character name (alter, real person) must never reach a public-facing music field. Case-insensitive WHOLE-WORD match so "Lex" does not fire inside "lexicon". When `roster` is None it defaults to the project's ``name_exposure.blocklist`` from MusicConfig; an empty roster yields zero hits (no-op).

## Example

```bash
agency-music-check_name_exposure --intent-id $IID …
```
