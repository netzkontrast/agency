<!-- agency-generated: v1 -->
# panel.convene

Convene the panel on a ``subject`` — emit a mode-appropriate multi-expert critique scaffold + record it (Spec 294).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (str — the plan/decision/document to analyse), mode (auto|discussion|debate|socratic), focus (balanced|full).` |  |  |

## Returns

``{panel_id, subject, mode, experts, analysis, synthesis}``.

## Chain-next

fill each lens/question; debate → re-convene as discussion.

## Details

``mode="auto"`` selects discussion / debate / socratic from the subject's content (decidable triggers). ``focus="full"`` convenes all nine experts; otherwise the most relevant 3-5 (or a balanced default).

## Example

```bash
agency-panel-convene --intent-id $IID …
```
