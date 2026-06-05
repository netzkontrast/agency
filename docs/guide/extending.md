# Extending Agency

Adding a capability is **adding a file**. The engine discovers it by reflection
and wires one tool per verb — no central registration, no per-tool boilerplate.

## A minimal capability

Drop a module in `agency/capabilities/` that defines a `CapabilityBase` subclass.
Set `name`/`home`, decorate verb-methods with `@verb(role=…)`, and reach the
engine's services through `self.ctx`:

```python
# agency/capabilities/greet.py
from ..capability import CapabilityBase, verb


class GreetCapability(CapabilityBase):
    name = "greet"
    home = "capability"

    @verb(role="transform")           # pure compute, no side effects
    def hello(self, who: str) -> dict:
        return {"result": f"hello, {who}"}
```

That's it. The engine `discover()`s `GreetCapability`, and `capability_greet_hello`
becomes callable over CLI, MCP, and code-mode. Verb parameters become the tool's
schema automatically (`inspect.signature`).

### Roles

- **`act`** — writes a crafted artefact (return an `{"artefact": {…}}` and the
  engine records a `PRODUCES` edge).
- **`transform`** — pure compute (lint, checklist, recommendations).
- **`effect`** — touches the world (subprocess, network, git). Effects should be
  verified — remember `COMPLETED ≠ done`.

### Reaching services via `self.ctx`

`self.ctx` is the one typed handle: `ctx.record`/`ctx.link` (write the graph),
`ctx.recall`/`ctx.find` (read), `ctx.call`/`ctx.spawn` (delegate to a sibling
capability — recorded as provenance, depth-guarded), `ctx.render`/`ctx.schema`
(templates/schemas), and `ctx.intent_id`. Composing capabilities is just
`self.ctx.call("other", "verb", **args)`.

## Owning your ontology

A capability owns its own slice of the schema via an `OntologyExtension`, merged
**strictly** onto the core (you may not redefine a core node):

```python
from ..ontology import OntologyExtension

class GreetCapability(CapabilityBase):
    name = "greet"
    ontology = OntologyExtension(
        nodes={"Greeting": ["who", "text"]},     # new node type + required fields
        enums={("Greeting", "lang"): {"en", "de"}},   # closed enum on a field
        edges={"GREETS"},                         # new edge type
        skills={...}, schemas={...}, templates={...},  # all optional
    )
```

Every field you add is enforced live in Memory on `record`/`link`/`update`.

## Out-of-tree extensions (the `examples/` pattern)

Domain capabilities don't belong in the core — they load through the engine's
extension point, so the bootstrapping harness stays minimal:

```python
from agency.engine import Engine
from examples.music import MusicCapability

engine = Engine("graph.db", extra_capabilities=[MusicCapability.as_capability()])
```

`examples/music.py` is a full worked example — a domain capability (an album
conceptualizer) that contributes a 7-phase gated skill, an `Album` node type, and
a closed enum, registering and extending the ontology exactly like a core
capability without shipping in core.

## Skills (walkable disciplines)

A skill is a Lifecycle template — an ordered list of phases, each declaring what
it must `produce`, optionally ending in a hard gate. Contribute one via your
`OntologyExtension(skills=…)` OR a file-based skill (Spec 060 folder form). A
phase can be **bound to a verb** (`"invoke": {"capability": …, "verb": …}`) so
that walking it *executes*; an unbound phase is a document step. See
`agency/capabilities/develop/_main.py` and `agency/capabilities/plugin/_main.py`
for shipped examples.

### File-based templates + schemas (Spec 060)

Drop strict artefact schemas under `<cap>/schemas/<name>.json` and rendering
templates under `<cap>/templates/<name>.md`. The engine's bootstrap loader
(Spec 060 §Phase 1) auto-discovers both and merges them into the capability's
`OntologyExtension`. The `<!-- AGENT: -->` blocks in templates are stripped
at render time for human output but remain visible when an agent reads the
file directly — the Bitwize pattern that lets templates BOTH render artefacts
AND instruct the agent on how to use them.

## After adding a capability

Regenerate the self-hosted install so the `help` map + plugin manifest reflect
the new surface, then verify lint + tests:

```bash
python -m agency.install        # regenerate plugin install + hooks + help skill
scripts/check-drift             # confirm install + tag inventory is clean
python -m pytest -q -n auto -m "not e2e"
```

To run the seven-rule capability lint against your new cap:

```bash
python -c "
from agency.engine import Engine
from agency.capabilities.plugin import lint_capability
e = Engine(':memory:')
print(lint_capability(e.registry.get('<your-cap>')))
"
```
