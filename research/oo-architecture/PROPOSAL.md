# Architecture Proposal: Object-Oriented Redesign of the Agency Plugin

Following first-principles decomposition and a pre-mortem inversion analysis mapped in `FINDINGS.md`, four gaps in the current PR1 object model require remediation.

## 1. Uniform `ToolResult` Envelope

### Precedent
`vendor/the-agency-system/Plan/decisions/0005-shared-toolresult-envelope.md:1` (URL: https://github.com/netzkontrast/the-agency-system.git, SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22).

### Python Sketch
```python
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class ToolResult:
    ok: bool
    data: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None
    next_suggested_tools: Optional[List[str]] = None
    error: Optional['TypedError'] = None
```

### Before/After
**Before (`agency/capabilities/jules.py:53`):**
```python
# Capability act returning an ad-hoc dict
def dispatch(self, prompt: str, source: str) -> dict:
    backend = self.ctx.inject(JulesBackend)
    res = backend.create(prompt, source, "main")
    return {"status": "dispatched", "url": res["url"]}
```

**After:**
```python
def dispatch(self, prompt: str, source: str) -> ToolResult:
    driver = self.ctx.get_driver("jules")
    res = driver.dispatch({"prompt": prompt, "source": source, "branch": "main"})
    return res
```

**Migration Cost:** Moderate. Requires migrating return signatures for all core capabilities to the new dataclass.

## 2. Generalised `Boundary` / `Driver` Protocol Family

### Precedent
`vendor/the-agency-system/Plan/decisions/0004-five-handler-domains.md:1` (URL: https://github.com/netzkontrast/the-agency-system.git, SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22) maps dynamic routing. `bitwize-music` pipeline scaling requires this pattern to support decoupled driver clusters.

### Python Sketch
```python
from typing import Protocol

class Boundary(Protocol):
    """Marker protocol for injected external boundaries."""
    pass

class Driver(Protocol):
    async def dispatch(self, task: dict) -> ToolResult:
        ...

class DriverRegistry:
    def register(self, name: str, driver: Driver) -> None:
        ...
    def get(self, name: str) -> Driver:
        ...
```

**Migration Cost:** Low. Eliminates hardcoded `JulesBackend` and `VCSBackend` in favor of generic driver dependency injection across orchestrator tasks.

## 3. First-Class `Phase` / `Skill` Objects

### Precedent
`agency/lifecycle.py:33` Models agent state effectively.

### Python Sketch
```python
from dataclasses import dataclass
from typing import List, Callable, Optional

@dataclass
class Phase:
    name: str
    required_outputs: List[str]
    gate: Optional[Callable[..., bool]] = None

    def validate(self, context: dict) -> bool:
        return all(req in context for req in self.required_outputs)

class Skill:
    def __init__(self, name: str, phases: List[Phase]):
        self.name = name
        self.phases = phases
        self._current_idx = 0

    def current(self) -> Phase:
        return self.phases[self._current_idx]
```

### Before/After
**Before (`agency/skill.py:40`):**
```python
def current(self) -> Optional[dict]:
    # Returns raw untyped dict
```

**After (`agency/skill.py:40`):**
```python
def current(self) -> Optional[Phase]:
    # Returns strong Phase object enforcing validation boundaries
```

**Migration Cost:** High. Re-authoring JSON manifests into Object definitions inside the `agency` engine requires a major refactoring pass but guarantees structural loop recovery.

## 4. Typed Error Handling

### Precedent
`vendor/the-agency-system/Plan/decisions/0011-repair-authority-tiers.md:1` (URL: https://github.com/netzkontrast/the-agency-system.git, SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22).

### Python Sketch
```python
from enum import Enum

class ErrorType(Enum):
    VALIDATION_FAILED = "validation_failed"
    DEPENDENCY_MISSING = "dependency_missing"
    GATE_FAILED = "gate_failed"

@dataclass
class TypedError:
    code: ErrorType
    message: str
    context: Optional[dict] = None
```

**Migration Cost:** Moderate. Will allow programmatic Engine loops to halt explicitly on `GATE_FAILED` without arbitrary `try/catch` heuristics.
