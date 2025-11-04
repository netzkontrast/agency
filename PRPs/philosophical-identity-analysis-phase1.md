name: "Philosophical Identity Analysis Platform (PIAP) - Phase 1 MVP"
description: |
  Build a bilingual (German + English) multi-agent system with 6 specialized philosophical agents
  for exploring truth theories and identity frameworks through education and research tools.

---

## Goal

Build Phase 1 MVP of the Philosophical Identity Analysis Platform:
- **All 6 philosophical agents** implemented with Pydantic AI (Correspondence, Coherence, Pragmatist, Synthesizer, Socratic, Research)
- **Bilingual architecture** (German + English) from ground up
- **Education-focused tools** for teaching truth theories and identity frameworks
- **Research-focused tools** for philosophical literature analysis
- **CLI interface** with rich formatting and agent routing
- **RAG system** with German philosophical paper + English translation + Stanford Encyclopedia entries
- **Full test coverage** with bilingual support

## Why

- **Fill a gap**: No existing tool makes rigorous philosophical frameworks operationally useful for both education and research
- **Democratize philosophy**: Make academic philosophy accessible and practical
- **Enable new insights**: Multi-agent analysis provides perspectives impossible for single-agent systems
- **Bilingual from start**: Serve both German and English-speaking philosophy communities
- **Open source**: MIT license allows community contribution and academic use

## What

A command-line tool that allows users to:
1. Learn about truth theories (correspondence, coherence, pragmatism) through interactive dialogue
2. Analyze identity conflicts using philosophical frameworks
3. Search and retrieve philosophical content in German or English
4. Get multi-perspective analysis from different philosophical agents
5. Conduct research on philosophical texts with proper citations

### Success Criteria
- [ ] All 6 agents functional and providing distinct philosophical perspectives
- [ ] Bilingual interface (German/English) with language switching
- [ ] RAG retrieval accuracy >90% for philosophical content (both languages)
- [ ] CLI provides rich, formatted output with tool call visibility
- [ ] Educational dialogues successfully teach truth theories
- [ ] Research tools can identify, classify, and cite philosophical concepts
- [ ] Test coverage >80% for all components
- [ ] Users can complete a full philosophical exploration session end-to-end
- [ ] German paper fully translated to English and embedded
- [ ] Philosophical glossary (German ↔ English) implemented

---

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Critical for implementation

- file: /home/user/agency/INITIAL.md
  why: Complete feature specification with all requirements

- file: /home/user/agency/CLAUDE.md
  why: Project conventions, code style, testing requirements

- file: /home/user/agency/use-cases/pydantic-ai/examples/main_agent_reference/
  why: Reference implementation for multi-agent architecture, CLI patterns, providers

- file: /home/user/agency/use-cases/pydantic-ai/examples/main_agent_reference/cli.py
  why: Rich CLI with streaming, tool call visibility - exact pattern to follow

- file: /home/user/agency/use-cases/pydantic-ai/examples/main_agent_reference/research_agent.py
  why: Multi-tool agent with dependencies pattern

- file: /home/user/agency/use-cases/pydantic-ai/examples/main_agent_reference/providers.py
  why: Multi-provider LLM configuration

- file: /home/user/agency/use-cases/pydantic-ai/examples/testing_examples/test_agent_patterns.py
  why: Testing patterns for Pydantic AI agents

- url: https://ai.pydantic.dev/
  section: Agents, Tools, Dependencies, Streaming
  why: Official Pydantic AI documentation for agent architecture

- url: https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
  why: Best practices for reducing hallucinations in philosophical content

- url: https://python.langchain.com/docs/concepts/vectorstores/
  why: ChromaDB and vector store patterns for RAG

- url: https://rich.readthedocs.io/
  why: Rich console formatting for beautiful CLI

- url: https://plato.stanford.edu/
  section: Truth, Identity, Correspondence Theory, Coherence Theory
  why: Stanford Encyclopedia of Philosophy - source for philosophical content

- content: German philosophical paper provided by user
  why: Primary source material - must be translated and embedded

```

### Current Codebase Structure

```bash
/home/user/agency/
├── CLAUDE.md                    # Project rules and conventions
├── INITIAL.md                   # Complete Phase 1 specification
├── README.md                    # Repository overview
├── PRPs/                        # Product Requirements Prompts
├── examples/                    # Will contain code examples (currently empty)
└── use-cases/
    └── pydantic-ai/
        └── examples/
            ├── main_agent_reference/     # **KEY REFERENCE**
            │   ├── research_agent.py
            │   ├── cli.py
            │   ├── providers.py
            │   ├── tools.py
            │   ├── models.py
            │   └── settings.py
            └── testing_examples/
                └── test_agent_patterns.py
```

### Desired Codebase Structure (Phase 1)

```bash
/home/user/agency/
├── piap/                                    # Main package
│   ├── __init__.py
│   ├── config.py                            # Configuration and settings
│   ├── i18n/                                # Internationalization
│   │   ├── __init__.py
│   │   ├── languages.py                     # Language detection and switching
│   │   ├── translations.py                  # Translation utilities
│   │   └── locales/
│   │       ├── de.json                      # German translations
│   │       └── en.json                      # English translations
│   ├── agents/                              # All 6 philosophical agents
│   │   ├── __init__.py
│   │   ├── base.py                          # Base agent configuration
│   │   ├── correspondence.py                # Correspondence theory agent
│   │   ├── coherence.py                     # Coherence theory agent
│   │   ├── pragmatist.py                    # Pragmatist theory agent
│   │   ├── synthesizer.py                   # Multi-perspective synthesizer
│   │   ├── socratic.py                      # Socratic questioning agent
│   │   ├── research.py                      # Research and literature agent
│   │   ├── prompts.py                       # System prompts (bilingual)
│   │   └── dependencies.py                  # Agent dependencies
│   ├── rag/                                 # RAG system
│   │   ├── __init__.py
│   │   ├── embeddings.py                    # Embedding generation
│   │   ├── vector_store.py                  # ChromaDB interface
│   │   ├── retrieval.py                     # Retrieval logic
│   │   └── indexing.py                      # Content indexing
│   ├── content/                             # Philosophical content
│   │   ├── __init__.py
│   │   ├── papers/
│   │   │   ├── german_paper_original.md    # Original German paper
│   │   │   └── german_paper_english.md     # English translation
│   │   ├── sep/                             # Stanford Encyclopedia excerpts
│   │   │   ├── correspondence_theory.md
│   │   │   ├── coherence_theory.md
│   │   │   ├── pragmatism.md
│   │   │   └── identity.md
│   │   ├── glossary.json                    # Bilingual philosophical terms
│   │   └── case_studies/                    # Example scenarios
│   │       ├── racism_identity.md
│   │       ├── body_image.md
│   │       └── narrative_fragmentation.md
│   ├── education/                           # Educational tools
│   │   ├── __init__.py
│   │   ├── tutoring.py                      # Interactive tutoring logic
│   │   ├── exercises.py                     # Practice exercises
│   │   └── lessons/                         # Structured lessons
│   │       ├── truth_theories.py
│   │       └── identity_frameworks.py
│   ├── research/                            # Research tools
│   │   ├── __init__.py
│   │   ├── literature_search.py             # Search philosophical content
│   │   ├── citation.py                      # Citation formatting
│   │   ├── theory_identification.py         # Classify philosophical positions
│   │   └── analysis.py                      # Identity conflict analysis
│   ├── cli/                                 # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py                          # Main CLI entry point
│   │   ├── commands.py                      # CLI commands
│   │   ├── formatting.py                    # Rich formatting utilities
│   │   └── router.py                        # Agent routing logic
│   └── models.py                            # Pydantic models
├── tests/                                   # Test suite
│   ├── __init__.py
│   ├── conftest.py                          # Pytest configuration
│   ├── test_agents/
│   │   ├── test_correspondence.py
│   │   ├── test_coherence.py
│   │   ├── test_pragmatist.py
│   │   ├── test_synthesizer.py
│   │   ├── test_socratic.py
│   │   └── test_research.py
│   ├── test_rag/
│   │   ├── test_embeddings.py
│   │   ├── test_retrieval.py
│   │   └── test_vector_store.py
│   ├── test_i18n/
│   │   ├── test_languages.py
│   │   └── test_translations.py
│   ├── test_education/
│   │   └── test_tutoring.py
│   ├── test_research/
│   │   └── test_literature_search.py
│   └── test_cli/
│       └── test_main.py
├── docs/                                    # Documentation
│   ├── README.md                            # User guide
│   ├── ARCHITECTURE.md                      # System architecture
│   └── API.md                               # API reference
├── data/                                    # Data storage
│   └── chroma_db/                           # Vector database
├── venv_linux/                              # Virtual environment
├── requirements.txt                         # Python dependencies
├── pyproject.toml                           # Project configuration
└── .env.example                             # Environment variables template
```

### Known Gotchas & Critical Patterns

```python
# CRITICAL: Pydantic AI Agent Patterns

# 1. Agent definition with deps_type
from pydantic_ai import Agent, RunContext

research_agent = Agent(
    get_llm_model(),  # From providers.py
    deps_type=ResearchAgentDependencies,  # Dataclass, NOT instances
    system_prompt=SYSTEM_PROMPT
)

# 2. Tools use RunContext for dependencies
@research_agent.tool
async def search_web(
    ctx: RunContext[ResearchAgentDependencies],  # Context provides deps
    query: str
) -> List[Dict[str, Any]]:
    # Access dependencies via ctx.deps
    api_key = ctx.deps.brave_api_key
    results = await search_tool(api_key, query)
    return results

# 3. Running agents with dependencies
deps = ResearchAgentDependencies(api_key="...")
result = await agent.run(prompt, deps=deps)

# 4. Streaming with Rich console (from cli.py pattern)
async with agent.iter(prompt, deps=deps) as run:
    async for node in run:
        if Agent.is_model_request_node(node):
            async with node.stream(run.ctx) as request_stream:
                async for event in request_stream:
                    if type(event).__name__ == "PartDeltaEvent":
                        # Stream text delta
                        console.print(event.delta.content_delta, end="")

# 5. Multi-provider support (from providers.py)
def get_llm_model():
    if settings.llm_provider == "openai":
        return "openai:gpt-4o"
    elif settings.llm_provider == "anthropic":
        return "anthropic:claude-sonnet-4"
    # Supports: openai, anthropic, groq, gemini, ollama

# CRITICAL: ChromaDB for bilingual RAG

# 1. Create collection with metadata filtering
import chromadb

client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_or_create_collection(
    name="philosophical_content",
    metadata={"hnsw:space": "cosine"}  # Cosine similarity
)

# 2. Add documents with language metadata
collection.add(
    documents=[text],
    metadatas=[{"language": "de", "source": "german_paper", "section": "part1"}],
    ids=[unique_id]
)

# 3. Query with language filtering
results = collection.query(
    query_texts=[query],
    n_results=5,
    where={"language": "de"}  # Filter by language
)

# CRITICAL: i18n Pattern

# 1. Store translations in JSON
# locales/en.json
{
  "cli.welcome": "Welcome to PIAP",
  "agents.correspondence.name": "Correspondence Agent"
}

# 2. Load with language detection
import json
import locale

def load_translations(lang: str) -> dict:
    with open(f"locales/{lang}.json") as f:
        return json.load(f)

# 3. Use with fallback
def t(key: str, lang: str = "en") -> str:
    """Translate key with fallback to English."""
    translations = load_translations(lang)
    return translations.get(key, load_translations("en").get(key, key))

# CRITICAL: Testing Patterns (from test_agent_patterns.py)

# 1. Mock dependencies, never mock agent logic
@pytest.fixture
def mock_deps():
    return ResearchAgentDependencies(
        api_key="test_key",
        session_id="test_session"
    )

# 2. Test agent outputs, not internals
async def test_agent_response(mock_deps):
    result = await agent.run("test prompt", deps=mock_deps)
    assert result.data is not None
    assert isinstance(result.data, str)

# 3. Use pytest-asyncio for async tests
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected

# CRITICAL: Follow CLAUDE.md rules
# - Never create files >500 lines (split into modules)
# - Use virtual environment: venv_linux/bin/python
# - Type hints everywhere
# - Google-style docstrings
# - Pydantic models for all data structures
# - Prompts in separate prompts.py files
```

---

## Implementation Blueprint

### Phase 1.1: Project Foundation & i18n Infrastructure (Week 1)

**Task 1: Set up project structure and configuration**

```yaml
CREATE piap/__init__.py:
  - Package initialization
  - Version info

CREATE piap/config.py:
  - Environment variable loading with python-dotenv
  - Settings management with Pydantic
  - Default language configuration
  - LLM provider settings (mirror providers.py pattern)

CREATE pyproject.toml:
  - Project metadata
  - Dependencies: pydantic-ai, chromadb, rich, pytest, pytest-asyncio
  - Python version: >=3.10

CREATE requirements.txt:
  - Generated from pyproject.toml

CREATE .env.example:
  - LLM_PROVIDER=anthropic
  - ANTHROPIC_API_KEY=your_key_here
  - OPENAI_API_KEY=your_key_here
  - DEFAULT_LANGUAGE=en
  - CHROMA_DB_PATH=./data/chroma_db

MODIFY .gitignore:
  - ADD data/chroma_db/
  - ADD .env
  - ADD venv_linux/
```

**Task 2: Create bilingual i18n system**

```yaml
CREATE piap/i18n/__init__.py:
  - Export main functions

CREATE piap/i18n/languages.py:
  - detect_language(text: str) -> str  # Simple heuristic or langdetect
  - get_user_language() -> str  # From config or prompt
  - set_language(lang: str)  # Update session preference

CREATE piap/i18n/translations.py:
  - load_translations(lang: str) -> dict
  - t(key: str, lang: str, **kwargs) -> str  # Translate with interpolation
  - translate_prompt(prompt_key: str, lang: str) -> str

CREATE piap/i18n/locales/en.json:
  - All English UI strings
  - Agent names and descriptions
  - Error messages
  - CLI prompts and labels

CREATE piap/i18n/locales/de.json:
  - All German translations
  - Philosophical terms in German
  - CLI interface in German

CREATE tests/test_i18n/test_languages.py:
  - test_detect_language_german()
  - test_detect_language_english()
  - test_language_switching()

CREATE tests/test_i18n/test_translations.py:
  - test_load_translations_english()
  - test_load_translations_german()
  - test_translation_fallback()
  - test_translation_interpolation()
```

**Pseudocode for i18n/translations.py:**

```python
import json
from pathlib import Path
from typing import Dict, Any

_translations_cache: Dict[str, Dict[str, str]] = {}

def load_translations(lang: str) -> Dict[str, str]:
    """
    Load translations from JSON file with caching.

    Args:
        lang: Language code (de, en)

    Returns:
        Dictionary of translations
    """
    # PATTERN: Cache translations to avoid repeated file reads
    if lang in _translations_cache:
        return _translations_cache[lang]

    # GOTCHA: Use Path for cross-platform compatibility
    locale_path = Path(__file__).parent / "locales" / f"{lang}.json"

    if not locale_path.exists():
        # PATTERN: Fallback to English if language not found
        lang = "en"
        locale_path = Path(__file__).parent / "locales" / "en.json"

    with open(locale_path, "r", encoding="utf-8") as f:
        translations = json.load(f)

    _translations_cache[lang] = translations
    return translations

def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """
    Translate a key with optional interpolation.

    Args:
        key: Translation key (e.g., "cli.welcome")
        lang: Language code
        **kwargs: Values for string interpolation

    Returns:
        Translated string
    """
    translations = load_translations(lang)

    # PATTERN: Nested key access with dots
    keys = key.split(".")
    value = translations

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # GOTCHA: Return key if translation missing (helps debug)
            return f"[MISSING: {key}]"

    # PATTERN: String interpolation if kwargs provided
    if kwargs and isinstance(value, str):
        try:
            return value.format(**kwargs)
        except KeyError as e:
            return f"[INTERPOLATION ERROR: {key}, missing {e}]"

    return str(value)
```

### Phase 1.2: Content Preparation & RAG System (Week 1-2)

**Task 3: Translate German paper and prepare content**

```yaml
CREATE piap/content/__init__.py:
  - Content loading utilities

TRANSLATE AND CREATE piap/content/papers/german_paper_english.md:
  - Full English translation of German philosophical paper
  - Preserve section structure and citations
  - Add metadata header (language, source, date)

COPY piap/content/papers/german_paper_original.md:
  - Original German text with metadata

FETCH AND CREATE piap/content/sep/*.md:
  - correspondence_theory.md (from Stanford Encyclopedia)
  - coherence_theory.md
  - pragmatism.md
  - identity.md
  - Each with proper attribution and URL

CREATE piap/content/glossary.json:
  - Bilingual philosophical terms dictionary
  {
    "Korrespondenztheorie": {
      "en": "Correspondence Theory",
      "definition_de": "...",
      "definition_en": "..."
    },
    ...
  }

CREATE piap/content/case_studies/*.md:
  - racism_identity.md (bilingual)
  - body_image.md (bilingual)
  - narrative_fragmentation.md (bilingual)
  - Each with analysis questions and theory applications
```

**Task 4: Build RAG system with bilingual support**

```yaml
CREATE piap/rag/__init__.py:
  - Export main classes

CREATE piap/rag/embeddings.py:
  - generate_embedding(text: str, model: str) -> List[float]
  - batch_generate_embeddings(texts: List[str]) -> List[List[float]]
  - PATTERN: Use sentence-transformers or OpenAI embeddings

CREATE piap/rag/vector_store.py:
  - class PhilosophicalVectorStore:
      - __init__(persist_directory: str)
      - add_document(text: str, metadata: dict, id: str)
      - add_documents(docs: List[Document])
      - query(query: str, n_results: int, lang: Optional[str]) -> List[Result]
      - query_with_filter(query: str, filter: dict) -> List[Result]
  - PATTERN: Wrap ChromaDB with philosophical-specific methods

CREATE piap/rag/retrieval.py:
  - retrieve_relevant_passages(query: str, lang: str, n: int) -> List[Passage]
  - retrieve_by_theory(theory: str, lang: str) -> List[Passage]
  - retrieve_by_concept(concept: str, lang: str) -> List[Passage]
  - cross_lingual_retrieve(query: str, target_lang: str) -> List[Passage]

CREATE piap/rag/indexing.py:
  - index_philosophical_content() -> None  # Index all content on first run
  - reindex() -> None
  - get_index_stats() -> dict

CREATE tests/test_rag/test_embeddings.py:
  - test_generate_embedding()
  - test_batch_embeddings()

CREATE tests/test_rag/test_vector_store.py:
  - test_add_document()
  - test_query_with_language_filter()
  - test_cross_lingual_query()

CREATE tests/test_rag/test_retrieval.py:
  - test_retrieve_correspondence_theory()
  - test_retrieve_german_content()
  - test_retrieve_english_content()
```

**Pseudocode for rag/vector_store.py:**

```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Document:
    """Philosophical document for indexing."""
    text: str
    metadata: Dict[str, Any]  # Must include 'language', 'source'
    id: str

@dataclass
class RetrievalResult:
    """Result from vector store query."""
    text: str
    metadata: Dict[str, Any]
    distance: float
    id: str

class PhilosophicalVectorStore:
    """
    Vector store specialized for philosophical content with bilingual support.

    Features:
    - Language-specific querying
    - Cross-lingual semantic search
    - Theory-based filtering
    - Citation preservation
    """

    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """
        Initialize vector store.

        Args:
            persist_directory: Path to ChromaDB storage
        """
        # PATTERN: Use persistent client for data survival across runs
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # PATTERN: Separate collections for different content types
        self.philosophical_texts = self.client.get_or_create_collection(
            name="philosophical_texts",
            metadata={"hnsw:space": "cosine"}
        )

        self.case_studies = self.client.get_or_create_collection(
            name="case_studies",
            metadata={"hnsw:space": "cosine"}
        )

    def add_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        doc_id: str
    ) -> None:
        """
        Add a single philosophical document.

        Args:
            text: Document text
            metadata: Must include 'language', 'source', 'theory' (optional)
            doc_id: Unique identifier
        """
        # CRITICAL: Validate required metadata
        if "language" not in metadata:
            raise ValueError("Metadata must include 'language' field")
        if "source" not in metadata:
            raise ValueError("Metadata must include 'source' field")

        # PATTERN: Route to appropriate collection
        collection = (
            self.case_studies
            if metadata.get("type") == "case_study"
            else self.philosophical_texts
        )

        # GOTCHA: ChromaDB requires lists for all parameters
        collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def query(
        self,
        query: str,
        n_results: int = 5,
        lang: Optional[str] = None,
        theory_filter: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Query for relevant philosophical passages.

        Args:
            query: Search query
            n_results: Number of results
            lang: Filter by language (de/en)
            theory_filter: Filter by philosophical theory

        Returns:
            List of retrieval results with text and metadata
        """
        # PATTERN: Build filter dict based on parameters
        where_filter = {}
        if lang:
            where_filter["language"] = lang
        if theory_filter:
            where_filter["theory"] = theory_filter

        # GOTCHA: Empty dict means no filtering
        query_params = {
            "query_texts": [query],
            "n_results": n_results
        }

        if where_filter:
            query_params["where"] = where_filter

        results = self.philosophical_texts.query(**query_params)

        # PATTERN: Convert to structured results
        retrieved = []
        for i in range(len(results["ids"][0])):
            retrieved.append(RetrievalResult(
                text=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                distance=results["distances"][0][i],
                id=results["ids"][0][i]
            ))

        return retrieved
```

### Phase 1.3: Build All 6 Philosophical Agents (Week 2-3)

**Task 5: Create base agent infrastructure**

```yaml
CREATE piap/models.py:
  - class PhilosophicalAnalysis(BaseModel)  # Structured analysis output
  - class IdentityConflict(BaseModel)  # Correspondence/coherence conflicts
  - class TheoryApplication(BaseModel)  # How theory applies to scenario
  - class Citation(BaseModel)  # Structured citations

CREATE piap/agents/__init__.py:
  - Export all agents

CREATE piap/agents/dependencies.py:
  - @dataclass PhilosophicalAgentDependencies:
      - vector_store: PhilosophicalVectorStore
      - language: str
      - session_id: Optional[str]
      - user_knowledge_level: str  # beginner, intermediate, advanced

CREATE piap/agents/base.py:
  - get_llm_model() -> str  # From config, supports multi-provider
  - create_base_agent(system_prompt: str, deps_type: Type) -> Agent
  - Common utilities for all agents

CREATE piap/agents/prompts.py:
  - CORRESPONDENCE_AGENT_PROMPT_EN: str
  - CORRESPONDENCE_AGENT_PROMPT_DE: str
  - COHERENCE_AGENT_PROMPT_EN: str
  - COHERENCE_AGENT_PROMPT_DE: str
  - PRAGMATIST_AGENT_PROMPT_EN: str
  - PRAGMATIST_AGENT_PROMPT_DE: str
  - SYNTHESIZER_AGENT_PROMPT_EN: str
  - SYNTHESIZER_AGENT_PROMPT_DE: str
  - SOCRATIC_AGENT_PROMPT_EN: str
  - SOCRATIC_AGENT_PROMPT_DE: str
  - RESEARCH_AGENT_PROMPT_EN: str
  - RESEARCH_AGENT_PROMPT_DE: str
  - get_prompt(agent_type: str, lang: str) -> str
```

**Task 6: Implement Correspondence Agent**

```yaml
CREATE piap/agents/correspondence.py:
  - correspondence_agent = Agent(...)
  - @tool search_correspondence_examples(ctx, concept: str)
  - @tool analyze_correspondence_conflict(ctx, statement: str)
  - @tool explain_correspondence_theory(ctx, level: str)
  - Focuses on truth-as-match-reality perspective
```

**Pseudocode for correspondence.py:**

```python
from pydantic_ai import Agent, RunContext
from typing import Dict, Any, List
from ..models import PhilosophicalAnalysis, IdentityConflict
from .dependencies import PhilosophicalAgentDependencies
from .base import get_llm_model
from .prompts import get_prompt

# Initialize agent with bilingual support
correspondence_agent = Agent(
    get_llm_model(),
    deps_type=PhilosophicalAgentDependencies,
    system_prompt=""  # Set dynamically based on language
)

@correspondence_agent.system_prompt
def get_system_prompt(ctx: RunContext[PhilosophicalAgentDependencies]) -> str:
    """
    Dynamic system prompt based on user language.

    Returns language-appropriate prompt for correspondence theory agent.
    """
    return get_prompt("correspondence", ctx.deps.language)

@correspondence_agent.tool
async def search_correspondence_examples(
    ctx: RunContext[PhilosophicalAgentDependencies],
    concept: str
) -> List[Dict[str, Any]]:
    """
    Search for examples and explanations of correspondence theory.

    Args:
        concept: Philosophical concept to search for

    Returns:
        List of relevant passages with citations
    """
    # PATTERN: Use vector store from dependencies
    results = ctx.deps.vector_store.query(
        query=concept,
        lang=ctx.deps.language,
        theory_filter="correspondence",
        n_results=3
    )

    # PATTERN: Format results with citations
    formatted = []
    for result in results:
        formatted.append({
            "text": result.text,
            "source": result.metadata.get("source"),
            "relevance": 1.0 - result.distance
        })

    return formatted

@correspondence_agent.tool
async def analyze_correspondence_conflict(
    ctx: RunContext[PhilosophicalAgentDependencies],
    statement: str,
    external_reality: str
) -> Dict[str, Any]:
    """
    Analyze a correspondence conflict (mismatch between belief and reality).

    Args:
        statement: User's self-concept or belief
        external_reality: External fact or social attribution

    Returns:
        Structured analysis of the conflict
    """
    # PATTERN: Structured analysis using philosophical framework

    # 1. Identify the claimed correspondence
    # 2. Identify the external reality
    # 3. Analyze the mismatch
    # 4. Reference relevant theory passages

    # GOTCHA: Must cite sources from RAG
    theory_refs = await search_correspondence_examples(ctx, "correspondence conflict")

    analysis = {
        "conflict_type": "correspondence",
        "self_concept": statement,
        "external_fact": external_reality,
        "gap_analysis": "...",  # AI generates this
        "theoretical_framework": theory_refs,
        "kant_problem": "This illustrates Kant's critique: you can never verify..."
    }

    return analysis

@correspondence_agent.tool
async def explain_correspondence_theory(
    ctx: RunContext[PhilosophicalAgentDependencies],
    level: str = "beginner"
) -> Dict[str, str]:
    """
    Explain correspondence theory at appropriate level.

    Args:
        level: beginner, intermediate, advanced

    Returns:
        Explanation tailored to knowledge level
    """
    # PATTERN: RAG retrieval for educational content
    query = f"correspondence theory explanation {level}"
    passages = ctx.deps.vector_store.query(
        query=query,
        lang=ctx.deps.language,
        n_results=2
    )

    return {
        "explanation": "...",  # AI synthesizes from passages
        "examples": "...",
        "key_thinkers": ["Aristotle", "Wittgenstein", "Tarski"],
        "sources": [p.metadata["source"] for p in passages]
    }
```

**Task 7-11: Implement remaining 5 agents**

```yaml
CREATE piap/agents/coherence.py:
  - coherence_agent = Agent(...)
  - @tool search_coherence_examples(ctx, concept: str)
  - @tool analyze_coherence_conflict(ctx, narrative: str)
  - @tool explain_coherence_theory(ctx, level: str)
  - Focuses on truth-as-systemic-consistency perspective

CREATE piap/agents/pragmatist.py:
  - pragmatist_agent = Agent(...)
  - @tool search_pragmatism_examples(ctx, concept: str)
  - @tool analyze_pragmatic_validity(ctx, belief: str, context: str)
  - @tool explain_pragmatism(ctx, level: str)
  - Focuses on truth-as-what-works perspective

CREATE piap/agents/synthesizer.py:
  - synthesizer_agent = Agent(...)
  - @tool synthesize_perspectives(ctx, analyses: List[Dict])
  - @tool identify_tensions(ctx, correspondence_view: str, coherence_view: str)
  - @tool recommend_framework(ctx, scenario: str)
  - Integrates multiple agent perspectives

CREATE piap/agents/socratic.py:
  - socratic_agent = Agent(...)
  - @tool ask_clarifying_question(ctx, user_statement: str)
  - @tool guide_exploration(ctx, topic: str, depth: int)
  - @tool route_to_specialist(ctx, query: str) -> str  # Returns agent name
  - Orchestrator that guides users and routes to specialists

CREATE piap/agents/research.py:
  - research_agent = Agent(...)
  - @tool search_literature(ctx, query: str, lang: str)
  - @tool identify_theory(ctx, passage: str) -> str
  - @tool generate_citation(ctx, source: str) -> str
  - @tool map_relationships(ctx, concept1: str, concept2: str)
  - Academic research and literature analysis
```

**Task 12: Create tests for all agents**

```yaml
CREATE tests/test_agents/conftest.py:
  - @fixture mock_vector_store
  - @fixture mock_philosophical_deps

CREATE tests/test_agents/test_correspondence.py:
  - test_search_correspondence_examples()
  - test_analyze_correspondence_conflict()
  - test_explain_correspondence_theory_beginner()
  - test_explain_correspondence_theory_advanced()
  - test_bilingual_prompts()

# Similar test files for other 5 agents
CREATE tests/test_agents/test_coherence.py
CREATE tests/test_agents/test_pragmatist.py
CREATE tests/test_agents/test_synthesizer.py
CREATE tests/test_agents/test_socratic.py
CREATE tests/test_agents/test_research.py
```

### Phase 1.4: Education & Research Tools (Week 3-4)

**Task 13: Build educational tutoring system**

```yaml
CREATE piap/education/__init__.py:
  - Export tutoring classes

CREATE piap/education/tutoring.py:
  - class TutoringSession:
      - __init__(topic: str, lang: str, level: str)
      - start_lesson() -> str
      - process_response(user_input: str) -> str
      - get_next_question() -> str
      - assess_understanding() -> float
  - Uses Socratic agent for guided learning

CREATE piap/education/lessons/truth_theories.py:
  - LESSON_STRUCTURE: dict  # Structured lesson plan
  - get_correspondence_lesson(level: str, lang: str) -> Lesson
  - get_coherence_lesson(level: str, lang: str) -> Lesson
  - get_pragmatism_lesson(level: str, lang: str) -> Lesson

CREATE piap/education/exercises.py:
  - class Exercise:
      - scenario: str
      - questions: List[str]
      - expected_concepts: List[str]
  - generate_exercise(theory: str, lang: str) -> Exercise
  - evaluate_answer(answer: str, expected: List[str]) -> float

CREATE tests/test_education/test_tutoring.py:
  - test_start_correspondence_lesson()
  - test_adaptive_difficulty()
  - test_bilingual_lessons()
```

**Task 14: Build research tools**

```yaml
CREATE piap/research/__init__.py:
  - Export research classes

CREATE piap/research/literature_search.py:
  - search_philosophical_content(query: str, lang: str, filters: dict) -> List[Result]
  - search_by_author(author: str, lang: str) -> List[Result]
  - search_by_theory(theory: str, lang: str) -> List[Result]
  - Uses research agent + RAG

CREATE piap/research/citation.py:
  - format_citation(source: dict, style: str) -> str  # APA, Chicago, MLA
  - generate_bibliography(sources: List[dict]) -> str
  - validate_citation(citation: str) -> bool

CREATE piap/research/theory_identification.py:
  - identify_philosophical_position(text: str) -> List[str]
  - classify_argument_type(argument: str) -> str
  - extract_key_concepts(text: str) -> List[str]
  - Uses research agent with specialized prompts

CREATE piap/research/analysis.py:
  - analyze_identity_narrative(narrative: str, lang: str) -> PhilosophicalAnalysis
  - identify_correspondence_conflicts(narrative: str) -> List[IdentityConflict]
  - identify_coherence_gaps(narrative: str) -> List[IdentityConflict]
  - synthesize_multi_agent_analysis(narrative: str) -> Dict[str, Any]
  - Coordinates multiple agents for comprehensive analysis

CREATE tests/test_research/test_literature_search.py:
  - test_search_by_theory()
  - test_bilingual_search()

CREATE tests/test_research/test_analysis.py:
  - test_analyze_identity_narrative()
  - test_multi_agent_synthesis()
```

**Pseudocode for research/analysis.py:**

```python
from typing import Dict, Any, List
from ..agents.correspondence import correspondence_agent
from ..agents.coherence import coherence_agent
from ..agents.pragmatist import pragmatist_agent
from ..agents.synthesizer import synthesizer_agent
from ..agents.dependencies import PhilosophicalAgentDependencies
from ..models import PhilosophicalAnalysis, IdentityConflict

async def synthesize_multi_agent_analysis(
    narrative: str,
    deps: PhilosophicalAgentDependencies
) -> Dict[str, Any]:
    """
    Coordinate multiple agents for comprehensive identity analysis.

    This is the flagship feature: show the power of multi-perspective analysis.

    Args:
        narrative: User's identity narrative or statement
        deps: Shared dependencies for all agents

    Returns:
        Comprehensive analysis from all perspectives
    """
    # PATTERN: Run agents in parallel for efficiency
    import asyncio

    # 1. Get correspondence perspective
    correspondence_task = correspondence_agent.run(
        f"Analyze this identity narrative from a correspondence theory perspective: {narrative}",
        deps=deps
    )

    # 2. Get coherence perspective
    coherence_task = coherence_agent.run(
        f"Analyze this identity narrative from a coherence theory perspective: {narrative}",
        deps=deps
    )

    # 3. Get pragmatist perspective
    pragmatist_task = pragmatist_agent.run(
        f"Analyze this identity narrative from a pragmatist perspective: {narrative}",
        deps=deps
    )

    # PATTERN: Await all analyses concurrently
    correspondence_result, coherence_result, pragmatist_result = await asyncio.gather(
        correspondence_task,
        coherence_task,
        pragmatist_task
    )

    # 4. Synthesize with synthesizer agent
    synthesis_prompt = f"""
I have three different philosophical analyses of an identity narrative:

Correspondence Theory Perspective:
{correspondence_result.data}

Coherence Theory Perspective:
{coherence_result.data}

Pragmatist Perspective:
{pragmatist_result.data}

Please synthesize these perspectives:
1. What do they agree on?
2. Where do they conflict?
3. What unique insights does each provide?
4. What is the most helpful framework for this specific case?
"""

    synthesis = await synthesizer_agent.run(synthesis_prompt, deps=deps)

    # CRITICAL: Return structured analysis with all perspectives
    return {
        "narrative": narrative,
        "correspondence_analysis": correspondence_result.data,
        "coherence_analysis": coherence_result.data,
        "pragmatist_analysis": pragmatist_result.data,
        "synthesis": synthesis.data,
        "language": deps.language
    }
```

### Phase 1.5: CLI Interface (Week 4)

**Task 15: Build CLI with agent routing**

```yaml
CREATE piap/cli/__init__.py:
  - Export CLI main function

CREATE piap/cli/main.py:
  - async def main() -> None  # Main entry point
  - MIRROR use-cases/pydantic-ai/examples/main_agent_reference/cli.py
  - Rich console with Panel, Prompt, Live streaming
  - Language selection on startup
  - Conversation history management

CREATE piap/cli/commands.py:
  - class Commands:
      - /help - Show available commands
      - /lang [de|en] - Switch language
      - /agent [name] - Switch to specific agent
      - /learn [topic] - Start educational tutorial
      - /research [query] - Research mode
      - /analyze [narrative] - Multi-agent identity analysis
      - /clear - Clear conversation history
      - /export - Export session to markdown

CREATE piap/cli/formatting.py:
  - format_agent_message(message: str, agent_name: str) -> Panel
  - format_tool_call(tool_name: str, args: dict) -> str
  - format_philosophical_analysis(analysis: dict) -> Panel
  - format_citation(citation: dict) -> str
  - Uses Rich for beautiful terminal output

CREATE piap/cli/router.py:
  - class AgentRouter:
      - route_query(query: str, lang: str) -> str  # Returns agent name
      - Uses Socratic agent to determine best specialist
  - route_to_agent(query: str, agent_name: str, deps: PhilosophicalAgentDependencies)

CREATE tests/test_cli/test_main.py:
  - test_cli_startup()
  - test_language_switching()
  - test_agent_routing()
```

**Pseudocode for cli/main.py (following use-case pattern exactly):**

```python
#!/usr/bin/env python3
"""
Bilingual philosophical CLI with multi-agent routing.

Usage:
    python -m piap.cli.main
"""

import asyncio
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from pydantic_ai import Agent

from ..agents.socratic import socratic_agent
from ..agents.correspondence import correspondence_agent
from ..agents.coherence import coherence_agent
from ..agents.pragmatist import pragmatist_agent
from ..agents.research import research_agent
from ..agents.synthesizer import synthesizer_agent
from ..agents.dependencies import PhilosophicalAgentDependencies
from ..rag.vector_store import PhilosophicalVectorStore
from ..i18n.languages import get_user_language, set_language
from ..i18n.translations import t
from .formatting import format_agent_message, format_tool_call
from .commands import process_command
from .router import AgentRouter

console = Console()

# PATTERN: Agent registry for routing
AGENTS = {
    "socratic": socratic_agent,
    "correspondence": correspondence_agent,
    "coherence": coherence_agent,
    "pragmatist": pragmatist_agent,
    "research": research_agent,
    "synthesizer": synthesizer_agent
}

async def stream_agent_interaction(
    agent: Agent,
    user_input: str,
    deps: PhilosophicalAgentDependencies,
    conversation_history: List[str]
) -> tuple[str, str]:
    """
    Stream agent interaction with real-time tool call display.

    CRITICAL: This function mirrors cli.py pattern exactly.
    """
    try:
        # Build context with conversation history
        context = "\n".join(conversation_history[-6:]) if conversation_history else ""

        prompt = f"""Previous conversation:
{context}

User: {user_input}

Respond naturally and helpfully in {deps.language}."""

        # Stream the agent execution (EXACT PATTERN from use-case)
        async with agent.iter(prompt, deps=deps) as run:
            response_text = ""

            async for node in run:
                if Agent.is_user_prompt_node(node):
                    pass  # Clean start

                elif Agent.is_model_request_node(node):
                    # Show assistant prefix at the start
                    console.print(f"[bold blue]{t('cli.assistant', deps.language)}:[/bold blue] ", end="")

                    # Stream model request events for real-time text
                    async with node.stream(run.ctx) as request_stream:
                        async for event in request_stream:
                            event_type = type(event).__name__

                            if event_type == "PartDeltaEvent":
                                if hasattr(event, 'delta') and hasattr(event.delta, 'content_delta'):
                                    delta_text = event.delta.content_delta
                                    if delta_text:
                                        console.print(delta_text, end="")
                                        response_text += delta_text
                            elif event_type == "FinalResultEvent":
                                console.print()  # New line after streaming

                elif Agent.is_call_tools_node(node):
                    # Stream tool execution events (CRITICAL for visibility)
                    async with node.stream(run.ctx) as tool_stream:
                        async for event in tool_stream:
                            event_type = type(event).__name__

                            if event_type == "FunctionToolCallEvent":
                                tool_name = "Unknown Tool"

                                if hasattr(event, 'part'):
                                    part = event.part
                                    if hasattr(part, 'tool_name'):
                                        tool_name = part.tool_name
                                    elif hasattr(part, 'function_name'):
                                        tool_name = part.function_name

                                # PATTERN: Use i18n for tool messages
                                console.print(format_tool_call(tool_name, deps.language))

                            elif event_type == "FunctionToolResultEvent":
                                result = str(event.tool_return) if hasattr(event, 'tool_return') else "No result"
                                if len(result) > 100:
                                    result = result[:97] + "..."
                                console.print(f"  ✅ [green]{t('cli.tool_result', deps.language)}:[/green] [dim]{result}[/dim]")

                elif Agent.is_end_node(node):
                    pass  # Keep it clean

        final_result = run.result
        final_output = final_result.output if hasattr(final_result, 'output') else str(final_result)

        return (response_text.strip(), final_output)

    except Exception as e:
        console.print(f"[red]❌ {t('cli.error', deps.language)}: {e}[/red]")
        return ("", f"Error: {e}")


async def main():
    """Main conversation loop."""

    # Initialize dependencies
    vector_store = PhilosophicalVectorStore()

    # Language selection
    console.print(Panel(
        "[bold]Select language / Sprache wählen[/bold]\n"
        "1. English\n"
        "2. Deutsch",
        style="blue"
    ))

    lang_choice = Prompt.ask("Language", choices=["1", "2"], default="1")
    language = "en" if lang_choice == "1" else "de"
    set_language(language)

    # Create dependencies
    deps = PhilosophicalAgentDependencies(
        vector_store=vector_store,
        language=language,
        session_id=None,
        user_knowledge_level="beginner"
    )

    # Show welcome
    welcome = Panel(
        f"[bold blue]{t('cli.welcome', language)}[/bold blue]\n\n"
        f"[green]{t('cli.description', language)}[/green]\n\n"
        f"[dim]{t('cli.help', language)}[/dim]",
        style="blue",
        padding=(1, 2)
    )
    console.print(welcome)
    console.print()

    conversation_history = []
    current_agent = "socratic"  # Start with Socratic agent
    router = AgentRouter()

    while True:
        try:
            # Get user input
            user_input = Prompt.ask(f"[bold green]{t('cli.you', language)}").strip()

            # Handle exit
            if user_input.lower() in ['exit', 'quit', 'ausgang']:
                console.print(f"\n[yellow]{t('cli.goodbye', language)}[/yellow]")
                break

            if not user_input:
                continue

            # Check for commands
            if user_input.startswith('/'):
                command_result = await process_command(user_input, deps, conversation_history)
                if command_result:
                    console.print(command_result)
                    console.print()
                continue

            # Route to appropriate agent (CRITICAL: Intelligent routing)
            if current_agent == "socratic":
                # Socratic agent decides if we need a specialist
                routing_prompt = f"Should this query go to a specialist agent? Query: {user_input}"
                routing_result = await socratic_agent.run(routing_prompt, deps=deps)

                # Parse routing decision (simplified - in production, use structured output)
                if "correspondence" in str(routing_result.data).lower():
                    current_agent = "correspondence"
                elif "coherence" in str(routing_result.data).lower():
                    current_agent = "coherence"
                elif "pragmatist" in str(routing_result.data).lower():
                    current_agent = "pragmatist"
                elif "research" in str(routing_result.data).lower():
                    current_agent = "research"

            # Add to history
            conversation_history.append(f"User: {user_input}")

            # Get agent
            agent = AGENTS[current_agent]

            # Show which agent is responding
            console.print(f"[dim][{t(f'agents.{current_agent}.name', language)}][/dim]")

            # Stream the interaction
            streamed_text, final_response = await stream_agent_interaction(
                agent,
                user_input,
                deps,
                conversation_history
            )

            # Handle the response display
            if streamed_text:
                console.print()
                conversation_history.append(f"Assistant: {streamed_text}")
            elif final_response and final_response.strip():
                console.print(f"[bold blue]{t('cli.assistant', language)}:[/bold blue] {final_response}")
                console.print()
                conversation_history.append(f"Assistant: {final_response}")
            else:
                console.print()

            # Reset to Socratic for next turn (it will route again if needed)
            current_agent = "socratic"

        except KeyboardInterrupt:
            console.print(f"\n[yellow]{t('cli.use_exit', language)}[/yellow]")
            continue

        except Exception as e:
            console.print(f"[red]{t('cli.error', language)}: {e}[/red]")
            continue


if __name__ == "__main__":
    asyncio.run(main())
```

**Task 16: Add setup.py and entry point**

```yaml
MODIFY pyproject.toml:
  - ADD [project.scripts]
      - piap = "piap.cli.main:main"
  - Enables: pip install -e . && piap

CREATE setup.py (if needed for backwards compatibility):
  - Entry point for CLI
```

### Phase 1.6: Final Integration & Testing (Week 4)

**Task 17: Create comprehensive integration tests**

```yaml
CREATE tests/test_integration_end_to_end.py:
  - @pytest.mark.asyncio
  - async def test_full_educational_session():
      # 1. Start with Socratic agent
      # 2. Request correspondence theory lesson
      # 3. Verify Socratic routes to education tools
      # 4. Complete lesson with Q&A
      # 5. Verify knowledge assessment

  - async def test_full_research_session():
      # 1. Query for "correspondence theory examples"
      # 2. Verify research agent is invoked
      # 3. Verify RAG retrieval
      # 4. Verify proper citations

  - async def test_multi_agent_identity_analysis():
      # 1. Provide identity narrative
      # 2. Verify all 3 theory agents are invoked
      # 3. Verify synthesizer integrates perspectives
      # 4. Verify structured output

  - async def test_bilingual_switching():
      # 1. Start in English
      # 2. Switch to German mid-conversation
      # 3. Verify all prompts and responses in German
      # 4. Verify RAG retrieves German content
```

**Task 18: Create content indexing script**

```yaml
CREATE scripts/index_content.py:
  - #!/usr/bin/env python3
  - Index all philosophical content into ChromaDB
  - Parse markdown files with metadata
  - Generate embeddings
  - Add to vector store with proper tags
  - Print indexing statistics

RUN: python scripts/index_content.py
  - Indexes German paper (original + translation)
  - Indexes SEP entries
  - Indexes case studies
  - Indexes glossary
```

**Task 19: Documentation**

```yaml
CREATE docs/README.md:
  - Quick start guide
  - Installation instructions
  - Basic usage examples
  - Command reference
  - FAQ

CREATE docs/ARCHITECTURE.md:
  - System architecture diagram
  - Agent responsibilities
  - Data flow
  - Bilingual architecture explanation

CREATE docs/API.md:
  - Python API documentation
  - How to use agents programmatically
  - How to add new agents
  - How to add new philosophical content

UPDATE README.md:
  - Project overview
  - Installation: pip install -e .
  - Usage: piap
  - Development setup
  - Testing: pytest tests/
  - Contributing guidelines
```

---

## Validation Loop

### Level 1: Syntax & Style

```bash
# CRITICAL: Run these FIRST before any other validation

# Activate virtual environment
source venv_linux/bin/activate

# Format code with black (if installed, otherwise skip)
black piap/ tests/ || echo "Black not installed, skipping formatting"

# Check with ruff (fix what's auto-fixable)
ruff check piap/ tests/ --fix

# Type checking with mypy
mypy piap/ --strict

# Expected: No errors. If errors exist:
# 1. READ the error message carefully
# 2. FIX the code
# 3. Re-run validation
```

### Level 2: Unit Tests (Progressive)

```bash
# PATTERN: Test incrementally as you build

# Test i18n system
pytest tests/test_i18n/ -v
# Expected: All translation and language tests pass

# Test RAG system
pytest tests/test_rag/ -v
# Expected: Embedding, retrieval, and vector store tests pass

# Test each agent individually
pytest tests/test_agents/test_correspondence.py -v
pytest tests/test_agents/test_coherence.py -v
pytest tests/test_agents/test_pragmatist.py -v
pytest tests/test_agents/test_synthesizer.py -v
pytest tests/test_agents/test_socratic.py -v
pytest tests/test_agents/test_research.py -v
# Expected: All agent-specific tests pass

# Test education and research tools
pytest tests/test_education/ -v
pytest tests/test_research/ -v
# Expected: Tutoring and research tool tests pass

# Test CLI (may require mocking)
pytest tests/test_cli/ -v
# Expected: CLI routing and formatting tests pass

# CRITICAL: All unit tests together
pytest tests/ -v --ignore=tests/test_integration_end_to_end.py
# Expected: >80% coverage, all tests passing

# Generate coverage report
pytest tests/ --cov=piap --cov-report=html --cov-report=term
# Expected: Coverage >80%
```

### Level 3: Integration Tests

```bash
# CRITICAL: These test full user workflows

# First, ensure content is indexed
python scripts/index_content.py

# Run integration tests
pytest tests/test_integration_end_to_end.py -v -s
# Expected: All end-to-end workflows complete successfully

# Test bilingual functionality specifically
pytest tests/test_integration_end_to_end.py::test_bilingual_switching -v -s
# Expected: Language switching works, retrieves correct language content

# Test multi-agent coordination
pytest tests/test_integration_end_to_end.py::test_multi_agent_identity_analysis -v -s
# Expected: All agents contribute to analysis, synthesizer integrates
```

### Level 4: Manual Testing (CLI)

```bash
# CRITICAL: Test actual user experience

# Start the CLI
python -m piap.cli.main

# Test 1: Language Selection
# - Select German
# - Verify UI is in German
# - Ask "Was ist die Korrespondenztheorie?"
# - Verify German response with German sources

# Test 2: Educational Tutoring
# - Type: /learn correspondence
# - Complete interactive lesson
# - Answer questions
# - Verify progression and understanding assessment

# Test 3: Research Tools
# - Type: /research "identity fragmentation"
# - Verify literature search results
# - Verify proper citations
# - Verify bilingual results

# Test 4: Multi-Agent Analysis
# - Type: /analyze "I identify as German but society sees me as foreign"
# - Verify correspondence agent identifies conflict
# - Verify coherence agent analyzes narrative
# - Verify pragmatist evaluates function
# - Verify synthesizer provides integrated insights

# Test 5: Agent Routing
# - Ask general question
# - Verify Socratic agent handles it
# - Ask specific theoretical question
# - Verify routing to appropriate specialist agent

# Test 6: Language Switching
# - Start in English
# - Type: /lang de
# - Verify all subsequent interactions in German
# - Verify RAG retrieves German content
```

### Level 5: Content Validation

```bash
# CRITICAL: Ensure philosophical accuracy

# Verify German paper translation quality
# - Read piap/content/papers/german_paper_english.md
# - Check against original
# - Verify philosophical terms are correctly translated

# Verify RAG retrieval accuracy
python -m piap.cli.main
# Query: "correspondence theory Kant"
# Expected: Retrieves passages about Kant's critique
# Verify: Correct passages, proper citations

# Query in German: "Kohärenztheorie Neurath"
# Expected: Retrieves German passages about Neurath
# Verify: German content, correct sources

# Test glossary
# Query: "What is adaequatio rei et intellectus?"
# Expected: Correct definition, German and English terms

# Philosophical accuracy check
# - Test each agent's core competency
# - Verify correspondence agent correctly applies correspondence theory
# - Verify coherence agent correctly applies coherence theory
# - Verify no philosophical hallucinations or misattributions
```

---

## Final Validation Checklist

- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check piap/ tests/`
- [ ] No type errors: `mypy piap/ --strict`
- [ ] Test coverage >80%: `pytest --cov=piap --cov-report=term`
- [ ] All 6 agents respond with distinct perspectives
- [ ] Bilingual UI works (German and English)
- [ ] RAG retrieval accuracy >90% (tested manually)
- [ ] CLI provides rich, formatted output
- [ ] Tool calls visible during streaming
- [ ] Agent routing works intelligently
- [ ] Educational tutoring flows naturally
- [ ] Research tools retrieve and cite properly
- [ ] Multi-agent analysis integrates all perspectives
- [ ] Language switching works mid-conversation
- [ ] German paper fully translated and indexed
- [ ] Glossary functional (German ↔ English)
- [ ] Documentation complete (README, ARCHITECTURE, API)
- [ ] Entry point works: `piap` command launches CLI
- [ ] Manual testing scenarios all successful

---

## Anti-Patterns to Avoid

### Code Anti-Patterns
- ❌ **Don't hardcode prompts in agent files** - Use prompts.py with bilingual support
- ❌ **Don't create files >500 lines** - Split into modules (per CLAUDE.md)
- ❌ **Don't skip type hints** - Every function must have type annotations
- ❌ **Don't use sync functions in async context** - All I/O should be async
- ❌ **Don't mock agent logic in tests** - Mock dependencies, not intelligence

### Philosophical Anti-Patterns
- ❌ **Don't let agents hallucinate sources** - All citations must be from RAG
- ❌ **Don't confuse theories** - Correspondence agent must not use coherence arguments
- ❌ **Don't oversimplify** - Maintain philosophical rigor even for beginners
- ❌ **Don't ignore citations** - Every claim should reference source material
- ❌ **Don't let synthesizer pick sides** - It integrates, doesn't judge

### Bilingual Anti-Patterns
- ❌ **Don't mix languages in single response** - Unless explicitly requested
- ❌ **Don't translate philosophical terms literally** - Use established translations
- ❌ **Don't default to English** - Respect user's language preference
- ❌ **Don't forget metadata** - All content must have language tags

### CLI Anti-Patterns
- ❌ **Don't hide tool calls** - Show users what agents are doing (transparency)
- ❌ **Don't print raw JSON** - Format everything with Rich panels
- ❌ **Don't interrupt streaming** - Let responses flow naturally
- ❌ **Don't route every query** - Let Socratic agent handle general questions

---

## Success Metrics & Confidence Score

### Quantitative Metrics
1. **Test Coverage**: Target >80%, Expected: 85-90%
2. **RAG Accuracy**: Target >90%, Test with known queries
3. **Response Time**: <2s for simple queries, <5s for multi-agent analysis
4. **Agent Distinctiveness**: Each agent should use <30% overlapping language

### Qualitative Metrics
1. **Philosophical Rigor**: Expert review of agent outputs (post-Phase 1)
2. **Educational Effectiveness**: Can a beginner learn correspondence theory?
3. **User Experience**: Is the CLI intuitive and beautiful?
4. **Bilingual Quality**: Are German responses natural, not translated-sounding?

### PRP Confidence Score: **8.5/10**

**Strengths (+):**
- ✅ Comprehensive context from INITIAL.md and use-case examples
- ✅ Clear patterns from main_agent_reference/
- ✅ Structured, phased approach with validation gates
- ✅ Bilingual architecture planned from ground up
- ✅ All 6 agents specified with distinct responsibilities
- ✅ Education + Research focus clearly defined
- ✅ Testing strategy comprehensive
- ✅ Anti-patterns documented

**Risks (-):**
- ⚠️ German paper translation quality depends on execution (not automated)
- ⚠️ RAG accuracy depends on embedding model choice (not specified)
- ⚠️ Agent routing logic is heuristic (may need refinement)
- ⚠️ Philosophical accuracy validation requires domain expertise (not automated)

**Mitigation:**
- Use professional translation for German paper (or native speaker review)
- Start with OpenAI embeddings (text-embedding-3-small) - proven quality
- Iterate on routing logic based on early testing
- Include philosophical accuracy checklist in manual validation

**Estimated Time to Completion**: 4-6 weeks (as planned)
- Week 1: Foundation + i18n + content prep
- Week 2: RAG + first 3 agents
- Week 3: Remaining 3 agents + tools
- Week 4: CLI + integration + testing

**Recommendation**: Proceed with implementation. This PRP provides sufficient context for successful one-pass execution with iterative refinement through validation loops.
