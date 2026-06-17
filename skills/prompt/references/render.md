<!-- agency-generated: v1 -->
# prompt.render

Fill a framework's template with ``fields`` → a PromptInstance (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `framework_slug (str), fields (dict — component→value), max_tokens (int).` |  |  |

## Returns

``{result, artefact: {kind, framework_slug, rendered_body, instance_id, approx_tokens}}`` OR ``{error}``.

## Chain-next

``prompt.evaluate(body, target='user-prompt')`` to score it.

## Details

Renders one ``COMPONENT: value`` line per framework component (the slots derived from the template), filling from ``fields`` (matched by component name, case-insensitive) and marking unfilled slots ``[TODO]``. Honors ``max_tokens`` (refuses an over-budget body — the ``engineer`` gate). Records a ``PromptInstance`` + a ``FILLS_FRAMEWORK`` edge to a lazily-recorded ``PromptFramework`` node (304 — nodes appear only on use; declare-an-edge ⇒ traverse-it).

## Example

```bash
agency-prompt-render --intent-id $IID …
```
