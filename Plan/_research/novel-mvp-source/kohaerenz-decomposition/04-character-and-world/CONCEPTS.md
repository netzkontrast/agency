# Character & World Concepts (Slice 4)

## 1. Character Model

The character capabilities defined in `skills/novel-architect-character/` map directly to the plugin's core primitives. This subsystem concerns populating the Narrative Context Protocol (NCP) player slots (`players[]`, `players[].motivations[]`, `players[].perspectives[]`) leveraging psychological frameworks.

### Plugin Mapping
*   **Intent**: To deeply develop a character for a given narrative slot, ensuring their psychological plausibility or archetypal function.
*   **Capability**: Character generation and psychological modeling, encapsulated under the `novel-architect-character` skill. The methods library acts as specific capability verbs (e.g., `generate_ocean_profile`, `map_jungian_arc`).
*   **Lifecycle**: Operates within "Phase 3: Character Architecture" of the broader `novel-architect` workflow. It’s an on-demand operation per character slot.
*   **Memory**: The graph stores the selected psychological models (`intent.methods_preference.character`), the resulting profile data, and the linkage to specific `players[]` and their Dramatica roles.

### Framework Modularity
The core idea is *progressive disclosure* and *pluggability*. The frameworks are separated into specific markdown files (`methods/`) and invoked selectively:
*   **Load-Bearing**: The generic capability to associate *some* psychological or motivational data with an NCP player slot is load-bearing. The relationship mapping to Dramatica roles (e.g., Protagonist vs. Main Character) via `dramatica-theory` is also foundational (see `SKILL.md`).
*   **Optional/Pluggable**: The specific models themselves (Big Five/OCEAN for realistic drama `big-five.md`, Enneagram for motivation `enneagramm.md`, Jung Archetypes for mythical/coming-of-age `jung-archetypes.md`, and TSDP/IFS for trauma `tsdp-ifs.md`) are optional and selectable per project or even per character.

### NCP and Dramatica Mapping
The plugin handles filling `narratives[].subtext.players[]` and their `motivations`/`perspectives` in the NCP. The orchestrator delegates this, but crucial resolution (Dramatica-Slot-Resolution via `nav.py`) must occur *before* NCP writes to ensure the character fulfills the correct structural role (e.g., ensuring the Ego in Jung maps appropriately to the MC perspective).

## 2. World Model

The world capabilities defined in `skills/novel-architect-world/` focus on constructing the setting and conducting deep research.

### Plugin Mapping
*   **Intent**: To build a coherent, well-researched world, identifying domains and executing targeted research briefs.
*   **Capability**: Worldbuilding and research delegation (`novel-architect-world`). It provides verbs for domain mapping (`methods/domain-mapping.md`) and writing research briefs (`methods/deep-research-briefs.md`). Crucially, the *execution* of research is delegated elsewhere (to `research-prompt-optimizer`).
*   **Lifecycle**: Operates in "Phase 4: World & Research". It has a distinct lifecycle: map domains -> draft briefs -> wait for external research agent -> integrate findings into `world-bible.md` and canon. This involves a User-Approval gate to protect canon.
*   **Memory**: The graph captures the initial genre-to-domain mapping, the state of the research brief (pending, executing, completed), and the provenance of findings before they are rendered into the world bible.

### Domain Mapping & World Bible
The domain mapping (`methods/domain-mapping.md`) uses heuristics to move from Genre -> Domain -> Depth (e.g., Hard-SF implies Physics/Cog Sci; "engine" depth implies exhaustive primary source research). This establishes the scope. The output is a set of domains to research. The World Bible (`world-bible.md`) is the ultimate rendered artefact aggregating these findings.

### Research-Brief Lifecycle
The `methods/deep-research-briefs.md` file defines a clear lifecycle pattern:
1.  **Draft**: Write `<domain>.md` brief.
2.  **Gate**: Ask user "Hand off to research-prompt-optimizer?". (This maps perfectly to the `BLOCKED_ON` + `input-required` gate in the plugin model).
3.  **Execute (External)**: `research-prompt-optimizer` takes over.
4.  **Integrate**: Findings (`research/findings/<domain>.md`) are returned and integrated into the world bible.
