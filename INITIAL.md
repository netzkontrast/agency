## FEATURE: Philosophical Identity Analysis Platform (PIAP)

A comprehensive multi-agent system for exploring the intersection of epistemology, identity theory, and practical self-understanding. The platform bridges rigorous philosophical analysis with accessible tools for self-exploration, education, and research.

### PRIMARY GOALS (in priority order):

1. **Education**: Teach truth theories and identity frameworks through interactive exploration
2. **Research**: Provide tools for philosophical analysis, literature mapping, and theory synthesis
3. **Self-Exploration**: Help users analyze their own identity narratives using philosophical frameworks
4. **Practical Support**: Offer frameworks for navigating identity conflicts and fragmentation

**Note**: Phase 1 focuses primarily on Education + Research capabilities, with self-exploration tools added in Phase 2.

### TARGET USERS:

- **Primary**: Philosophy students, academics, and therapists seeking theoretical frameworks
- **Secondary**: General public experiencing identity questions or crises
- **Tertiary**: Researchers in philosophy, psychology, cultural studies, and related fields

### CORE VALUE PROPOSITION:

**"The first system that makes rigorous philosophical frameworks for identity operationally useful for both academic research and personal self-understanding."**

What exists now:
- Academic philosophy papers (inaccessible, static)
- Therapy tools (lacks philosophical rigor)
- AI chatbots (superficial, no structured frameworks)

What this provides:
- Multi-agent system where different agents embody different philosophical positions
- Structured analysis tools that apply epistemological frameworks to identity
- Research capabilities for philosophical literature
- Visualization of identity conflicts through philosophical lenses

---

## TECHNICAL ARCHITECTURE:

### Stack:
- **Backend**: FastAPI (Python) - REST API architecture
- **Agents**: Pydantic AI with multi-provider support (OpenAI, Anthropic, local models)
- **Database**: PostgreSQL for sessions, SQLite for embedded philosophical content
- **Frontend**: Initially CLI, Phase 2 adds web interface (React/Next.js)
- **RAG**: Embedded vector store (ChromaDB) for philosophical texts
- **i18n**: Bilingual from start (German + English) - content, UI, and agent responses

**✅ CONFIRMED DECISIONS:**
- **License**: MIT (open source, permissive)
- **Development Style**: Methodical 4-phase approach (personal project, no hard deadlines)
- **Phase 1 Scope**: All 6 agents implemented immediately
- **Priority**: Education + Research tools first

### Multi-Agent Design:

**Specialized Philosophical Agents:**
1. **Correspondence Agent**: Analyzes identity through correspondence theory lens
2. **Coherence Agent**: Analyzes identity through coherence theory lens
3. **Pragmatist Agent**: Applies pragmatic truth theory to identity questions
4. **Synthesizer Agent**: Integrates multiple perspectives, identifies tensions
5. **Socratic Agent**: Conducts guided questioning and exploration
6. **Research Agent**: Literature search, citation analysis, theory mapping

**Orchestration:**
- Central coordinator routes user queries to appropriate agent(s)
- Agents can consult each other for multi-perspective analysis
- Session manager maintains conversation context and user models

### Database Schema:
```
users (id, created_at, preferences)
sessions (id, user_id, started_at, context)
conversations (id, session_id, agent_type, messages)
analyses (id, session_id, analysis_type, results, visualizations)
philosophical_content (id, type, source, embedding, metadata)
case_studies (id, scenario, analyses, outcomes)
```

---

## PHILOSOPHICAL DEPTH & SCOPE:

### Phase 1 Content:
- Core truth theories: Correspondence, Coherence, Pragmatism, Consensus
- Identity frameworks: Modern unified self, Postmodern fragmentation, Narrative identity
- Psychological mechanisms: Cognitive dissonance, Self-discrepancy, Narrative construction
- **Primary source**: The provided German paper (with full English translation)

### Phase 2 Expansion:
- Deflationary theories, Minimalism, Pluralism about truth
- Psychoanalytic identity (Freud, Lacan, Kristeva)
- Neuroscientific perspectives (embodied cognition, predictive processing)
- Non-Western frameworks: Buddhist anatman, Daoist Wu Wei, Ubuntu philosophy

### Phase 3 Advanced:
- Formal logical modeling of identity structures
- Original synthesis capabilities (system generates novel philosophical insights)
- Multi-modal philosophical analysis (text, image, behavior patterns)

### Knowledge Representation:
- Create formal ontologies for truth theories and identity concepts
- Represent logical relationships, contradictions, and implications
- Enable reasoning about which frameworks apply to which scenarios

---

## FUNCTIONALITY - PHASED APPROACH:

### PHASE 1 - MVP (Core Philosophical Agent System)

**🎯 FOCUS: Education + Research Tools**

**MUST HAVE - ALL 6 AGENTS:**
1. **Correspondence Agent**: Analyzes through correspondence theory lens
2. **Coherence Agent**: Analyzes through coherence theory lens
3. **Pragmatist Agent**: Applies pragmatic truth theory
4. **Synthesizer Agent**: Integrates perspectives, identifies tensions
5. **Socratic Agent**: Conducts guided questioning and exploration
6. **Research Agent**: Literature search, citation analysis, theory mapping

**MUST HAVE - CORE FEATURES:**
1. **Interactive Dialogue** (Socratic questioning via CLI)
   - Natural conversation with all 6 specialized agents
   - Multi-turn context retention
   - Intelligent agent routing and handoffs
   - **Bilingual**: German + English interface and responses

2. **Philosophical Tutoring** (Education Priority)
   - Teach truth theories through examples and dialogue
   - Connect theories to identity applications
   - Adaptive difficulty based on user knowledge
   - Interactive exercises and case studies
   - **Bilingual**: Content in both German and English

3. **Research Tools** (Research Priority)
   - RAG-based search of philosophical content
   - Retrieve relevant passages from source paper(s)
   - Proper citation and source attribution
   - Theory identification and classification
   - Literature mapping capabilities
   - **Bilingual**: Search and retrieve in both languages

4. **Identity Mapping** (Text-based initially)
   - Identify correspondence conflicts (self-concept vs. external facts)
   - Identify coherence gaps (narrative inconsistencies)
   - Output structured analysis with theory references
   - Multi-agent analysis showing different perspectives

**MUST HAVE - BILINGUAL SUPPORT:**
- All agent prompts available in German and English
- Philosophical content in both languages
- CLI supports language switching
- Users can interact in either language
- Responses adapt to user's language preference

**NICE TO HAVE:**
- Export analysis results to markdown/PDF (bilingual)
- Save and resume sessions
- Basic visualization (ASCII art diagrams)
- Mixed-language conversations (switch mid-session)

### PHASE 2 - Self-Analysis Framework

**MUST HAVE:**
1. **Narrative Analysis**
   - User provides life story/identity statement
   - System analyzes for coherence, gaps, contradictions
   - Identifies correspondence vs. coherence tensions

2. **Correspondence-Gap Identifier**
   - Structured assessment of discrepancies
   - Self-concept vs. social attribution conflicts
   - Actual vs. ideal vs. ought self analysis

3. **Practical Recommendations**
   - Concrete strategies based on philosophical framework
   - Not therapy, but philosophically-grounded guidance
   - Reference to relevant psychological research

4. **Visualization Dashboard** (Web interface)
   - Visual identity maps showing conflicts
   - Timeline of narrative coherence
   - Theory application diagrams

**NICE TO HAVE:**
- Comparative analysis (multiple sessions over time)
- Export detailed reports
- Shareable anonymized analyses

### PHASE 3 - Research & Education Platform

**MUST HAVE:**
1. **Interactive Theory Explorer**
   - Visual, interactive explanations of all theories
   - Case studies with multiple philosophical interpretations
   - Historical context and development

2. **Literature Analysis Tools**
   - Upload philosophical papers for analysis
   - Citation network mapping
   - Theory identification and classification

3. **Extensible Framework**
   - Plugin system for adding new philosophical theories
   - Community-contributed case studies
   - Modular agent architecture

**NICE TO HAVE:**
- Discussion forums
- Collaborative analysis sessions
- Integration with Zotero/academic tools

### PHASE 4 - Clinical/Therapeutic Tools

**MUST HAVE:**
1. **Crisis Navigation Protocols**
   - Structured support for acute identity crises
   - Clear boundaries (not therapy, referral mechanisms)
   - Evidence-based philosophical interventions

2. **Privacy-First Architecture**
   - Local processing option
   - Encrypted storage
   - User data ownership and deletion

3. **Professional Tools**
   - Therapist/coach dashboard
   - Client session summaries
   - Integration with clinical frameworks (CBT, ACT, etc.)

---

## USER EXPERIENCE FLOW:

### Entry Points (User Choice):

**Mode 1: Exploratory Chat**
- "I have questions about identity/truth/self"
- Socratic agent guides open-ended exploration
- System suggests relevant frameworks dynamically

**Mode 2: Structured Assessment**
- Questionnaire to identify correspondence/coherence conflicts
- Generates initial identity map
- Offers paths for deeper exploration

**Mode 3: Tutorial Mode**
- "Teach me about truth theories"
- Systematic education with examples
- Progressive complexity

**Mode 4: Research Mode**
- "Analyze this philosophical text"
- "Find papers on X theory"
- Professional research tools

### Interaction Modes:
- **Primary (Phase 1)**: CLI chat interface
- **Secondary (Phase 2)**: Web chat + visual dashboard
- **Tertiary (Phase 3)**: API for integration into other tools

### Output Formats:
- **Conversational**: Natural language explanations and insights
- **Structured**: Markdown reports with sections, citations, diagrams
- **Visual**: D3.js/Mermaid diagrams of identity structures and conflicts
- **Actionable**: Concrete suggestions and frameworks for navigation

### Privacy & Ethics:

**Core Principles:**
1. **Transparency**: Always clear that this is AI, not human therapist
2. **Boundaries**: Clear about what system can/cannot do
3. **Referral**: Built-in crisis resources and professional referrals
4. **Consent**: Explicit opt-in for data storage, easy deletion
5. **Anonymization**: All stored examples stripped of identifying info

**Implementation:**
- Local-first option (all processing on user machine)
- Opt-in cloud sync for multi-device
- No data sharing without explicit consent
- Regular ethics review of system outputs

---

## CONTENT STRATEGY:

### Philosophical Texts:

**Phase 1 (BILINGUAL from start):**
- **German**: The provided German philosophical paper (primary source - original)
- **English**: Full English translation of the German paper (to be created)
- **English**: Stanford Encyclopedia of Philosophy entries on truth and identity
- **German/English**: Key excerpts from cited sources (Kant, Frege, Stuart Hall, etc.)
- **Bilingual**: Synthetic case studies based on paper's examples
- **Both languages**: Glossary of philosophical terms with translations

**Bilingual Architecture:**
- All content stored with language tags (de/en)
- RAG retrieval supports queries in both languages
- Cross-language semantic search (query in German, get English results and vice versa)
- Parallel corpus approach where possible

**Phase 2:**
- Crawl4AI MCP to fetch additional papers (German and English sources)
- User-uploaded texts for analysis (language auto-detected)
- Community-contributed philosophical content (multilingual)

**Phase 3:**
- Integration with PhilPapers, JSTOR (English + German philosophy databases)
- Automated literature review capabilities (multilingual)
- Dynamic knowledge base updates

### Case Studies & Examples:

**Sources:**
1. **Historical Figures**: Philosophers who struggled with identity (Nietzsche, Kierkegaard, etc.)
2. **Literary Characters**: Complex identities from literature (requires analysis, not real people)
3. **Synthetic Scenarios**: Carefully crafted examples covering common patterns
4. **Anonymized Real Stories** (Phase 4 only, with strict consent)

**Coverage:**
- Racism and cultural identity conflicts
- Body image and social media (correspondence crisis)
- Career/role transitions (coherence disruption)
- LGBTQ+ identity navigation
- Immigration and cultural fragmentation
- Religious deconversion/conversion

### Multimedia:

**Phase 1**: Text only (CLI)

**Phase 2**:
- Mermaid diagrams for theory relationships
- D3.js visualizations for identity maps
- Animated explanations of philosophical concepts

**Phase 3**:
- Video explainers (generated or curated)
- Interactive philosophy simulations
- Gamified learning modules

---

## INTEGRATION & EXTENSIBILITY:

### MCP Servers:

**Phase 1:**
- **Filesystem MCP**: Read philosophical texts from organized folders
- **SQLite MCP**: Manage embedded content database

**Phase 2:**
- **Crawl4AI MCP**: Fetch and process philosophical papers
- **PostgreSQL MCP**: Manage user sessions and analyses

**Phase 3:**
- **Custom Philosophy MCP**: Specialized tools for philosophical analysis
- **Zotero MCP** (if available): Integration with citation management

### APIs & External Integration:

**Phase 1**: None (standalone)

**Phase 2:**
- Crisis Text Line / 988 suicide hotline integration
- Philosophy Stack Exchange (read-only)

**Phase 3:**
- PhilPapers API for literature search
- ORCID for researcher profiles
- Mental health referral databases

**Phase 4:**
- Electronic health record integration (for clinical use)
- Teletherapy platform plugins

### Plugin Architecture:

**Design:**
```python
class PhilosophicalFramework(Protocol):
    def analyze_identity(self, narrative: str) -> Analysis: ...
    def generate_questions(self, context: Context) -> List[Question]: ...
    def evaluate_coherence(self, statements: List[str]) -> CoherenceScore: ...
```

**Enables:**
- Third parties can add new philosophical theories
- Community can contribute cultural perspectives
- Researchers can test novel frameworks

---

## EVALUATION & VALIDATION:

### Success Metrics:

**Quantitative:**
1. **Engagement**: Session length, return rate, completion rate
2. **Understanding**: Pre/post-tests on philosophical concepts
3. **Utility**: User ratings, export frequency, recommendation rate
4. **Technical**: Response time, accuracy of RAG retrieval, agent handoff success

**Qualitative:**
1. **Philosophical Rigor**: Expert review of system outputs
2. **User Testimonials**: Deep interviews on value provided
3. **Case Studies**: Documentation of impactful uses
4. **Academic Reception**: Citations, integration into curricula

### Quality Control:

**Philosophical Accuracy:**
- All agent responses cite sources
- Regular review by philosophy graduate students/professors
- Red-team testing with deliberately bad philosophy
- Version control for philosophical content with academic review

**Ethical Safety:**
- Review outputs for harmful content (e.g., encouraging self-harm)
- Test with mental health professionals
- Regular audits of crisis navigation responses
- User reporting mechanism for problematic outputs

### User Feedback:

**Mechanisms:**
1. **Post-session survey**: Quick rating + optional comment
2. **Detailed feedback form**: For users who want to elaborate
3. **A/B testing**: Different agent behaviors, prompts, UI elements
4. **Usage analytics**: What features are used, what's ignored
5. **Academic collaboration**: Partner with universities for structured studies

---

## DEVELOPMENT APPROACH:

### Phasing Strategy:

**PHASE 1: Core Philosophical Agent System (4-6 weeks)**
- Multi-agent architecture with ALL 6 agents (Correspondence, Coherence, Pragmatist, Synthesizer, Socratic, Research)
- **Bilingual system architecture** (German + English from ground up)
- CLI interface for interaction (with language selection)
- RAG system with German paper + English translation + SEP entries
- **Education-focused**: Interactive tutoring on truth theories
- **Research-focused**: Literature search and citation tools
- Basic identity mapping (text output)
- Session persistence with language preferences
- Unit tests for all components
- **Translation infrastructure**: i18n framework, language detection, bilingual prompts

**Deliverables:**
- Working bilingual CLI tool
- 6 specialized agents with distinct perspectives
- RAG retrieval with 90%+ accuracy (both languages)
- Test coverage >80%
- Bilingual documentation for developers and users
- English translation of German philosophical paper
- Glossary of philosophical terms (German ↔ English)

**PHASE 2: Self-Analysis Framework (4-6 weeks)**
- Narrative analysis agent
- Structured assessment tools
- Web interface (FastAPI + React)
- Visual identity mapping
- PostgreSQL database
- Export functionality

**Deliverables:**
- Web application
- Comprehensive assessment tools
- Visual dashboards
- Expanded test suite
- User guide

**PHASE 3: Research & Education Platform (6-8 weeks)**
- Interactive theory explorer
- Literature analysis tools
- Plugin architecture
- Community features
- Expanded philosophical content
- API for third-party integration

**Deliverables:**
- Full-featured platform
- Public API with documentation
- Plugin SDK
- Academic partnerships
- Published research on system

**PHASE 4: Clinical Tools (8-12 weeks)**
- Crisis protocols with expert review
- Privacy-first architecture
- Professional dashboard
- Clinical integration
- Extensive safety testing
- Regulatory compliance (HIPAA if US, GDPR if EU)

**Deliverables:**
- Clinical-grade tool
- Certification/approval from relevant bodies
- Training materials for professionals
- Comprehensive safety documentation

### Testing Strategy:

**Unit Tests:**
- Each agent's core reasoning functions
- RAG retrieval accuracy
- Database operations
- API endpoints

**Integration Tests:**
- Multi-agent conversations
- End-to-end user flows
- Session persistence across interactions

**Philosophical Validity Tests:**
- Outputs reviewed by philosophy experts
- Comparison to expected analysis on known cases
- Consistency across agents (do they represent their theories accurately?)

**User Testing:**
- Alpha: Developers and philosophers
- Beta: Small group of target users (students, therapists)
- Public: Phased rollout with monitoring

**Safety Testing:**
- Red team for harmful outputs
- Mental health expert review
- Edge case handling (crisis situations)

### Documentation:

**Developer Documentation:**
- Architecture overview with diagrams
- Agent design patterns
- How to add new philosophical frameworks
- API reference
- Contribution guidelines

**User Documentation:**
- Getting started guide
- Theory explainers (non-technical)
- Example sessions with commentary
- FAQ
- Privacy policy and terms

**Academic Documentation:**
- White paper on system design and philosophical approach
- Validation studies
- Limitations and future work
- Ethical considerations

---

## EXAMPLES & PATTERNS:

### Similar Projects to Learn From:

1. **Eliza (1960s)**: Early psychotherapy chatbot - learn from interaction patterns
2. **Therapist.ai**: Modern AI therapy - study ethical boundaries
3. **Stanford Encyclopedia of Philosophy**: Content structure and rigor
4. **Obsidian/Roam**: Graph-based knowledge tools - inspiration for philosophy mapping
5. **Replika**: Personal AI companion - engagement patterns

### Interaction Style:

**Hybrid Approach - Context-Dependent:**

1. **Socratic** (Default for exploration):
   - "What do you mean when you say you 'feel torn'?"
   - "Can you think of a time when this conflict was especially strong?"
   - Never tells, always asks - guides user to insight

2. **Academic** (Tutorial mode and research):
   - "Kant's argument against correspondence theory proceeds as follows..."
   - Precise terminology, citations, formal structure
   - Appropriate for philosophy students and researchers

3. **Therapeutic** (Self-analysis mode - with clear boundaries):
   - "It sounds like there's a gap between how you see yourself and how others see you."
   - Empathetic, validating, but NOT therapy
   - Always includes: "This is philosophical exploration, not mental health treatment."

4. **Analytical** (Identity mapping):
   - "Based on your narrative, I've identified three correspondence conflicts and two coherence gaps."
   - Structured, clear, evidence-based
   - Shows work, cites framework

### Code Examples from `examples/`:

**Request: Please provide any relevant code examples from this repo's `examples/` folder**
- Multi-agent patterns (if they exist)
- Pydantic AI usage examples
- Tool/RAG implementations
- CLI interface patterns

---

## CONSTRAINTS & PREFERENCES:

### Timeline:
- **Phase 1 (MVP)**: Aim for 4-6 weeks to functional prototype
- **Overall**: Build for long-term (1-2 years to full platform)
- **Iterative**: Working software at end of each phase

### Code Style:
- Follow all conventions in CLAUDE.md
- **Additional**:
  - Type hints everywhere (use `typing` module)
  - Pydantic models for all data structures
  - Comprehensive docstrings in Google style
  - Agent prompts in separate `prompts.py` modules (not hardcoded)
  - Configuration via environment variables and/or YAML

### Deployment:
- **Phase 1**: Local CLI tool (pip installable)
- **Phase 2**: Self-hosted web app (Docker + docker-compose)
- **Phase 3**: Cloud deployment (optional, user choice)
- **Phase 4**: Enterprise deployment options

### Open Source Strategy:
- **Core system**: MIT or Apache 2.0 license (open source)
- **Philosophical content**: CC BY-SA 4.0 (share-alike)
- **Clinical tools (Phase 4)**: May require different licensing for liability

---

## INITIAL DEVELOPMENT PRIORITIES:

### Immediate Next Steps:

1. **Set up bilingual project structure** following CLAUDE.md conventions
2. **Create i18n framework** for German/English support
3. **Translate German paper to English** (first major content task)
4. **Create base agent architecture** with Pydantic AI (all 6 agents)
5. **Implement bilingual RAG system** with German + English content
6. **Build all 6 agents** (Correspondence, Coherence, Pragmatist, Synthesizer, Socratic, Research)
7. **Create bilingual CLI interface** with language selection
8. **Write comprehensive tests** (including language-specific tests)

### First Concrete Features to Implement:

1. **Feature: Bilingual System Foundation**
   - i18n framework with language detection
   - Configuration for user language preference
   - Bilingual prompt templates for all agents
   - Language-aware response formatting

2. **Feature: Educational Tutoring System**
   - Interactive lessons on correspondence theory
   - Interactive lessons on coherence theory
   - Interactive lessons on pragmatism
   - Case studies and exercises (bilingual)
   - Adaptive difficulty progression

3. **Feature: Research Tools Suite**
   - RAG-based bilingual search of philosophical content
   - Citation and source attribution
   - Theory identification and classification
   - Literature relationship mapping
   - Retrieve relevant passages in user's preferred language

4. **Feature: All 6 Philosophical Agents**
   - Correspondence Agent (analyzes via correspondence theory)
   - Coherence Agent (analyzes via coherence theory)
   - Pragmatist Agent (applies pragmatic truth theory)
   - Synthesizer Agent (integrates multiple perspectives)
   - Socratic Agent (conducts guided exploration)
   - Research Agent (literature search and analysis)

5. **Feature: Identity Conflict Analysis**
   - Multi-agent analysis from all perspectives
   - Identify correspondence conflicts
   - Identify coherence gaps
   - Synthesized insights
   - Outputs structured, cited analysis (bilingual)

---

## ✅ KEY DECISIONS CONFIRMED:

1. **Phasing**: 4-phase methodical approach (as planned)
2. **Technical stack**: Pydantic AI + FastAPI + CLI/Web ✓
3. **Phase 1 Scope**: ALL 6 agents (not just 4) ✓
4. **Open source**: MIT License ✓
5. **Priority**: Education + Research tools first ✓
6. **Content**: Bilingual from start (German + English) ✓
7. **Target**: Personal project, no hard deadlines ✓

---

## DREAM OUTCOME:

**Short-term (6 months):**
- Working multi-agent system used by philosophy students for learning
- Positive feedback from academics on philosophical rigor
- 100+ users actively exploring identity through the platform
- Published case studies of interesting analyses

**Medium-term (1-2 years):**
- Platform used in university philosophy courses
- Therapists using framework for client discussions (with supervision)
- Research papers published using the system's analysis capabilities
- Active community contributing case studies and frameworks

**Long-term (3-5 years):**
- Gold standard tool for philosophical identity exploration
- Integration into mental health and coaching practices
- Novel philosophical insights generated by the system
- Global community with non-Western philosophical frameworks integrated
- Demonstrable positive impact on users' self-understanding and wellbeing

**Ultimate Vision:**
"The system that finally makes rigorous philosophy not just accessible, but genuinely useful for navigating the complexity of modern identity - democratizing insights that were previously locked in academic papers and therapy offices."
