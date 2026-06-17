# agency-scaffold: v1
"""symbols — token-efficient symbol compression, first-class (Spec 300).

A native reimplementation of SuperClaude's Token-Efficiency symbol system
(`MODE_Token_Efficiency` + `BUSINESS_SYMBOLS`): a decidable phrase↔symbol
substitution that compresses prose for dense communication and expands it back.
Pure transforms (like `thinking`), so they compose anywhere; pairs with
`mode.token_efficiency` (the posture) — this is the mechanism.

Use when: output must be compact without losing meaning — large-scale results,
status digests, dense logic chains under a token budget.
Triggers:
- A token-constrained context that needs compressed output
- A status or logic digest that benefits from symbolic shorthand
- Expanding a symbol-dense note back into prose for a reader
Red flags:
- Padding a token-tight reply with prose → symbols.compress it
- Pasting symbol-dense text to a reader who needs prose → symbols.expand it
"""
from __future__ import annotations

import re

from ...capability import CapabilityBase, verb
from ...ontology import OntologyExtension


# phrase → symbol (longest phrases first so multi-word forms win). Extracted from
# SuperClaude's Token-Efficiency legend (logic/flow · status · domain).
_MAP: list[tuple[str, str]] = [
    ("transforms to", "⇒"), ("leads to", "→"), ("results in", "→"),
    ("causes", "→"), ("because", "∵"), ("therefore", "∴"), ("thus", "∴"),
    ("in progress", "🔄"), ("pending", "⏳"), ("waiting", "⏳"),
    ("completed", "✅"), ("passed", "✅"), ("succeeded", "✅"),
    ("failed", "❌"), ("error", "❌"), ("warning", "⚠️"),
    ("critical", "🚨"), ("urgent", "🚨"),
    ("performance", "⚡"), ("security", "🛡️"), ("analysis", "🔍"),
    ("configuration", "🔧"), ("deployment", "📦"), ("design", "🎨"),
    ("then", "»"),
]
# symbol → canonical phrase (for expand; first phrase that maps to each symbol).
_EXPAND: dict[str, str] = {}
for _phrase, _sym in _MAP:
    _EXPAND.setdefault(_sym, _phrase)


def _count(text: str) -> int:
    """Whitespace token count — a stable proxy for compression measurement."""
    return len(text.split())


class SymbolsCapability(CapabilityBase):
    name = "symbols"
    home = "memory"   # pure communication transforms
    ontology = OntologyExtension()

    @verb(role="transform")
    def legend(self) -> dict:
        """The phrase↔symbol legend.

        Inputs: (none).
        Returns: ``{count, legend: [{phrase, symbol}]}``.
        chain_next: symbols.compress(text) / symbols.expand(text).
        """
        return {"count": len(_MAP),
                "legend": [{"phrase": p, "symbol": s} for p, s in _MAP]}

    @verb(role="transform")
    def compress(self, text: str) -> dict:
        """Substitute known phrases with symbols — dense, decidable (Spec 300).

        Inputs: text (str).
        Returns: ``{compressed, original_tokens, compressed_tokens, reduction}``
                 (reduction = fraction of tokens saved).
        chain_next: symbols.expand to restore prose.
        """
        out = text
        for phrase, sym in _MAP:                      # longest-first by construction
            out = re.sub(rf"\b{re.escape(phrase)}\b", sym, out, flags=re.IGNORECASE)
        before, after = _count(text), _count(out)
        reduction = round((before - after) / before, 3) if before else 0.0
        return {"compressed": out, "original_tokens": before,
                "compressed_tokens": after, "reduction": reduction}

    @verb(role="transform")
    def expand(self, text: str) -> dict:
        """Expand symbols back into prose (the inverse of ``compress``).

        Inputs: text (str — symbol-dense).
        Returns: ``{expanded}``.
        chain_next: hand the prose to a reader who needs words, not symbols.
        """
        out = text
        for sym, phrase in _EXPAND.items():
            out = out.replace(sym, phrase)
        return {"expanded": out}
