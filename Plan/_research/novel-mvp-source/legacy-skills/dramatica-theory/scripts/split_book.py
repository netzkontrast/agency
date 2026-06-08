#!/usr/bin/env python3
"""Split the Dramatica book Markdown into thematic reference chunks.

Reads /home/claude/dramatica.md (output of pdf-to-markdown skill against
the source PDF) and writes 9 chunk files into ./references/.

Each chunk gets a written preamble describing what's in it and where it
sits in the source — so the SKILL.md can reference chunks by topic
without preloading them.

Boundaries are line-numbers verified against the source by inspecting
the headings. They cut at section starts; the last chunk runs to EOF.
"""

from __future__ import annotations

from pathlib import Path

SOURCE = Path("/home/claude/dramatica.md")
OUT_DIR = Path(__file__).parent.parent / "references"

# (filename, start_line, end_line_exclusive, title, preamble)
# Lines are 1-indexed to match `grep -n` output.
CHUNKS = [
    (
        "01-foundations.md",
        305, 445,
        "Foundations: Story Mind, Four Throughlines, Grand Argument Story",
        "What's here: the conceptual core. Story Mind premise (a complete "
        "story models one mind solving one problem), the four throughlines "
        "(Overall Story / Main Character / Impact Character / Subjective "
        "Story), and what makes a story a Grand Argument Story versus a "
        "Tale. Includes Star Wars and To Kill A Mockingbird worked through "
        "all four throughlines. Read this first if Dramatica is new to you.",
    ),
    (
        "02-characters.md",
        445, 1572,
        "Characters: Archetypes, Complex Characters, Drivers/Passengers, Motivation Elements",
        "What's here: every character topic in the book. The eight archetypes "
        "(Protagonist, Antagonist, Guardian, Contagonist, Reason, Emotion, "
        "Sidekick, Skeptic), how they split into Action and Decision "
        "characteristics, the Driver/Passenger quad, Motivation Elements "
        "(16 + the four motivation quads), Complex Characters in Gone With "
        "the Wind and Rear Window, and the introduction to Subjective "
        "Characters and the Crucial Element. Long file — search for "
        "specific archetype names or 'Crucial Element' to land where you "
        "need.",
    ),
    (
        "03-deep-theory.md",
        1572, 1794,
        "Deep Theory: Justification and Problem Solving",
        "What's here: the part of Dramatica that tries to explain why "
        "characters cling to broken solutions. Justification theory, "
        "problem-solving as story-engine, paradigms and givens, the "
        "Justified Main Character. Short but conceptually load-bearing — "
        "this is what underwrites the Change/Steadfast distinction.",
    ),
    (
        "04-theme.md",
        1794, 2422,
        "Theme: Throughlines, Concerns, Issues, Problems, Story Points",
        "What's here: theme as Dramatica defines it. The hierarchy "
        "Class → Type (Concern) → Variation (Issue) → Element (Problem), "
        "with each level worked through Star Wars examples. Throughline-"
        "to-Class assignments (Universe / Physics / Mind / Psychology) "
        "for OS, MC, IC, SS — including the 'Situation as MC Throughline' "
        "etc. matrix. The storyform synthesis. Additional story points at "
        "Element, Variation, and Type levels.",
    ),
    (
        "05-plot-genre.md",
        2422, 2942,
        "Plot and Genre: Story Points, Acts, Sequences, Scenes, Genre Modes",
        "What's here: plot structure proper. Plot vs Storyweaving (a "
        "distinction that matters in Dramatica). The eight plot story "
        "points — Goal, Requirements, Consequences, Forewarnings (static) "
        "and Dividends, Costs, Prerequisites, Preconditions (driver/"
        "passenger). Plot Progression: Acts (3- and 4-act), Sequences, "
        "Scenes, Events. Genre treated as Modes of Expression, with the "
        "grid of Dramatica genres.",
    ),
    (
        "06-storyforming.md",
        2942, 3910,
        "Storyforming (Stage 1): Dynamics and Story Point Selection",
        "What's here: the operational core of using Dramatica. Selecting "
        "throughlines. Picking the right Class for each. Character "
        "Dynamics (MC Resolve Change/Steadfast, MC Growth Start/Stop, "
        "MC Approach Do-er/Be-er, MC Mental Sex Linear/Holistic). Plot "
        "Dynamics (Story Driver Action/Decision, Story Limit Timelock/"
        "Optionlock, Outcome Success/Failure, Judgment Good/Bad). "
        "Selecting static plot story points (Goal, Reqs, Cons, "
        "Forewarnings, Dividends, Costs, Prereqs, Preconditions). "
        "Selecting thematic story points. Selecting character story "
        "points. The Crucial Element. Most of the actual decisions that "
        "produce a storyform live in this file.",
    ),
    (
        "07-storyencoding.md",
        3910, 4614,
        "Storyencoding (Stage 2): Dressing Structural Choices in Subject Matter",
        "What's here: how to encode an abstract storyform as concrete "
        "subject matter. Encoding archetypes vs complex characters. "
        "Encoding Mental Sex. Encoding theme for each throughline. "
        "Encoding plot. The big payoff in this chunk: Signposts and "
        "Journeys — the four-stage progression structure that maps the "
        "Type-level concern of each throughline through the four acts. "
        "Worked for OS, MC, IC, and SS throughlines separately. "
        "Encoding genre.",
    ),
    (
        "08-storyweaving-reception.md",
        4614, 5410,
        "Storyweaving (Stage 3) and Story Reception (Stage 4)",
        "What's here: how to arrange the encoded material into the actual "
        "narrative the audience experiences (acts, scenes, flashbacks, POV "
        "switches), and how to think about who the audience is. Spatial "
        "and temporal storyweaving techniques. Format-specific tips: "
        "short stories, episodic TV, multi-story ensemble / soap operas, "
        "novels, motion pictures (Rule of Threes, hand-offs, "
        "dismissals). The four stages of communication. Writing for "
        "self, others, and groups. Propaganda taxonomy (Shock / "
        "Awareness / Conditioning / Misdirection — useful for "
        "diagnosing manipulative narrative). Adaptation considerations.",
    ),
    (
        "09-reference.md",
        5410, 7517,
        "Reference: Epilogue, Vocabulary, Semantic Items, Structural Models",
        "What's here: the back-of-book reference. Epilogue, including a "
        "full worked Dramatica analysis of Jurassic Park. Vocabulary "
        "(alphabetical glossary with cross-references and synonyms — "
        "this is the file to load for any 'what does X mean' question). "
        "Semantic Items: the canonical lists of 4 Classes, 16 Types, "
        "64 Variations, 64 Elements. Structural Models showing how they "
        "nest. Largest file by far; use it as a lookup, not a read-through.",
    ),
]


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"source not found: {SOURCE}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SOURCE, encoding="utf-8") as fh:
        all_lines = fh.readlines()
    total_lines = len(all_lines)

    written = []
    for fname, start, end, title, preamble in CHUNKS:
        # 1-indexed inclusive start, exclusive end → slice [start-1:end-1]
        body_lines = all_lines[start - 1:end - 1]
        body = "".join(body_lines).rstrip() + "\n"

        header = (
            f"# {title}\n\n"
            f"> Source: Phillips & Huntley, *Dramatica: A New Theory of "
            f"Story* (4th ed., 2001), © Screenplay Systems Inc. "
            f"This chunk: source lines {start}–{end - 1} of "
            f"{total_lines}. Verbatim extract for personal narrative-"
            f"craft use; not for redistribution.\n\n"
            f"**{preamble}**\n\n"
            f"---\n\n"
        )

        out_path = OUT_DIR / fname
        out_path.write_text(header + body, encoding="utf-8")
        written.append((fname, len(body_lines), out_path.stat().st_size))

    # Summary
    print(f"Wrote {len(written)} chunks to {OUT_DIR}/")
    print(f"{'file':<32} {'lines':>8} {'bytes':>10}")
    print("-" * 52)
    for fname, lines, size in written:
        print(f"{fname:<32} {lines:>8,} {size:>10,}")


if __name__ == "__main__":
    main()
