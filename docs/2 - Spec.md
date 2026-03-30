# spec.md
## Product Specification — Non-Animal Research Alternatives Finder
**Version:** 1.0 — Hackathon build
**Status:** Approved for development
**Last updated:** Pre-execution

---

## 2.1 Project Definition

A web-based tool that accepts a description of an animal-based research methodology — as free text, a protocol summary, or a pasted abstract — and returns a structured set of validated non-animal alternatives. Each result is tagged with its source type (curated or LLM-inferred), validation status, regulatory acceptance context, and access path. Output can be exported in formats suitable for grant applications, ethics committee submissions, or R&D documentation. The system serves three user types — academic researchers, pharma/biotech R&D teams, and ethics committee reviewers — with role-aware output framing.

---

## 2.2 Features

| Feature | Tier |
|---|---|
| Free-text / protocol description input | Minimal |
| Semantic parsing of input to extract biological question + endpoint + model type | Minimal |
| Match against curated alternatives database | Minimal |
| LLM gap-filling for queries outside curated coverage | Minimal |
| Clear source-type flagging per result (curated vs. inferred) | Minimal |
| Validation status per alternative (ECVAM-validated / peer-reviewed / emerging) | Minimal |
| Basic citation / source link per result | Minimal |
| Role selection (researcher / pharma / ethics reviewer) | Minimal |
| Role-aware output framing (grant / regulatory / challenge language) | Minimal |
| Export to plain text / copy-to-clipboard | Minimal |
| Regulatory acceptance metadata by jurisdiction (OECD, FDA, EMA) | Full |
| Access/cost information per alternative | Full |
| Confidence score per result | Full |
| Saved searches and history | Full |
| PDF export formatted for ethics submissions | Full |
| Feedback loop — user can flag poor results to improve curation | Full |
| API for institutional integration | Extended |
| Community-contributed method updates (moderated) | Extended |
| Grant platform integrations | Extended |

---

## 2.3 UI Overview

### Screen 1 — Input
- Role selector: three buttons (Researcher / Pharma R&D / Ethics Reviewer) — sets output tone, not query logic
- Large textarea: "Describe the animal-based method or paste your protocol"
- Optional collapsible structured fields: study type, species, endpoint — to improve match quality when provided
- Submit → triggers parsing + matching pipeline

### Screen 2 — Results
- Intent summary bar at top: *"You described a [repeated-dose oral toxicity study]. Here are validated non-animal alternatives."* — confirms the system understood correctly before results are shown
- Result cards sorted: curated results first, then a visible divider labelled "AI-suggested alternatives", then inferred results below
- Coverage note displayed when inferencer was used: *"Some results were suggested by AI and may require independent verification."*
- Copy-to-clipboard export button

### Screen 3 — Result Detail (expanded card)
- Full description of the alternative
- Validation pathway and status
- Source citation in standard format
- Source URL link
- Regulatory context stub (Minimal: shows what curated data contains, no jurisdiction metadata)

---

## 2.4 Architecture

**Pattern: Modular monolith** for Minimal scope; designed for service extraction at Full.

A single deployable application with clearly separated internal modules: input processing, retrieval, LLM inference, result assembly, and output formatting. No microservices at this stage — overhead not justified, boundaries not yet proven. Modules are separated by interface contracts so they can be extracted later without a rewrite.

See `decisions.md` ADR-002 for rationale.

---

## 2.5 Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | React + TypeScript | Component model suits role-aware output; TS catches interface contract errors early |
| Backend | Python (FastAPI) | Strong NLP/AI ecosystem; lightweight and async-capable |
| LLM integration | Anthropic Claude API | Strong at scientific text parsing; reliable structured output; controllable generation |
| Vector DB | ChromaDB (Minimal) → Pinecone (Full) | ChromaDB is local and free for Minimal; Pinecone scales for Full |
| Relational DB | PostgreSQL | Curated alternatives data; structured, queryable, durable |
| Hosting | Railway or Render (Minimal) → AWS/GCP (Full) | Low ops overhead for Minimal; clear migration path |
| Build tooling | Vite (frontend), Alembic (DB migrations) | Standard choices, no lock-in |

---

## 2.6 Data Architecture

### Entities

```
AnimalMethod
  - id (uuid)
  - name (string)
  - description (text)
  - study_type (string)
  - endpoint_type (string)
  - species_replaced (string[])
  - synonyms (string[])

Alternative
  - id (uuid)
  - name (string)
  - description (text)
  - method_type (enum: in_vitro | in_silico | organoid | ex_vivo | other)
  - validation_status (enum: ecvam_validated | peer_reviewed | emerging | llm_inferred)
  - source_type (enum: curated | llm_inferred)
  - source_url (string | null)
  - citations (string[])
  - access_info (text | null)  ← stub for Minimal

AnimalMethod ←→ Alternative  (many-to-many join table with relevance_notes field)

RegulatoryRecord  ← Full tier only, stub at Minimal
  - alternative_id (fk)
  - jurisdiction (string)
  - acceptance_status (string)
  - guideline_reference (string)

UserQuery  ← logged for future improvement
  - id (uuid)
  - raw_input (text)
  - parsed_intent (jsonb)
  - results_returned (int)
  - role (string)
  - inferencer_used (bool)
  - timestamp
```

### Storage split
- **PostgreSQL:** All structured entity data — alternatives, methods, relationships, citations
- **ChromaDB:** Embeddings of alternative descriptions and method descriptions — used for semantic retrieval

---

## 2.7 Infrastructure

| Environment | Setup |
|---|---|
| Dev | Local Docker Compose — FastAPI + PostgreSQL + ChromaDB |
| Prod (Minimal) | Railway — single service deployment, managed PostgreSQL |
| Prod (Full) | Containerised services on AWS/GCP with managed vector DB |

CI: GitHub Actions — lint, test, deploy on merge to main.

---

## 2.8 Project Structure

```
/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── InputPanel/        # Role selector + textarea + optional fields
│   │   │   ├── ResultsPanel/      # Cards + curated/inferred divider + export
│   │   │   └── ResultCard/        # Individual result with badge logic
│   │   ├── hooks/                 # useQuery, API integration
│   │   ├── types/                 # Shared TypeScript interfaces (mirrors backend contracts)
│   │   └── utils/                 # Role-aware output formatters, clipboard
│   ├── public/
│   └── vite.config.ts
│
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── query.py           # POST /query
│   │       └── health.py          # GET /health
│   ├── modules/
│   │   ├── parser/
│   │   │   └── parser.py          # Input → ParsedIntent (Claude API)
│   │   ├── retriever/
│   │   │   └── retriever.py       # ParsedIntent → CuratedResult[] (PG + ChromaDB)
│   │   ├── inferencer/
│   │   │   └── inferencer.py      # ParsedIntent + gaps → InferredResult[] (Claude API)
│   │   ├── assembler/
│   │   │   └── assembler.py       # Merge + rank + tag → ResultSet
│   │   └── formatter/
│   │       └── formatter.py       # ResultSet + role → FormattedResponse
│   ├── db/
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── vector_store.py        # ChromaDB abstraction (swap to Pinecone at Full)
│   │   └── migrations/            # Alembic
│   ├── data/
│   │   ├── raw/                   # ECVAM / NC3Rs reference material
│   │   └── seed/
│   │       └── alternatives.json  # Hand-curated seed dataset (~25–40 entries)
│   ├── tests/
│   │   ├── test_parser.py
│   │   ├── test_retriever.py
│   │   └── test_pipeline.py
│   ├── main.py
│   └── requirements.txt
│
├── prompts/                       # Versioned AI agent prompt library
│   ├── PROMPT_IMPL_db-schema_v1.0.md
│   ├── PROMPT_IMPL_parser-module_v1.0.md
│   ├── PROMPT_IMPL_inferencer-module_v1.0.md
│   └── PROMPT_IMPL_result-card_v1.0.md
│
├── decisions.md
├── execution-log.md
├── dev-plan.md
└── spec.md                        ← this file
```

---

## 2.9 Module Responsibilities & Interface Contracts

### Modules

| Module | Responsibility | Boundary |
|---|---|---|
| **Parser** | Raw input + role → structured `ParsedIntent` via Claude API | Does not query DB. Handles vague input gracefully — partial extraction acceptable, never crashes. |
| **Retriever** | `ParsedIntent` → semantic search ChromaDB + metadata fetch PostgreSQL → `CuratedResult[]` | Knows nothing about LLM. Returns empty list if no matches — does not generate. |
| **Inferencer** | `ParsedIntent` + existing curated results → Claude API gap-fill → `InferredResult[]` | Only called when curated results < 3. All output tagged `llm_inferred`. No invented citations. |
| **Assembler** | Merges curated + inferred → deduplicates → ranks (curated first) → attaches coverage note | Pure data logic. No API calls. |
| **Formatter** | `ResultSet` + role → role-aware language and structure → `FormattedResponse` | Pure transformation. No data logic, no API calls. |

### Interface Contracts (Python / Pydantic)

```python
# Parser output
class ParsedIntent(BaseModel):
    study_type: str
    endpoint_type: str
    species: str | None
    assay_context: str | None
    raw_input: str

# Retriever output
class CuratedResult(BaseModel):
    alternative_id: str
    name: str
    description: str
    method_type: str
    validation_status: str
    source_url: str | None
    citations: list[str]
    relevance_score: float
    source_type: Literal["curated"] = "curated"

# Inferencer output
class InferredResult(BaseModel):
    name: str
    description: str
    method_type: str
    rationale: str           # Why this is relevant — mandatory, non-empty
    confidence: str          # "high" | "medium" | "low"
    source_type: Literal["llm_inferred"] = "llm_inferred"

# Assembler output
class ResultSet(BaseModel):
    parsed_intent: ParsedIntent
    results: list[CuratedResult | InferredResult]
    coverage_note: str | None    # Non-null when inferencer was used
    inferencer_used: bool

# Formatter output
class FormattedResponse(BaseModel):
    role: str
    intent_summary: str          # "You described a [X]. Here are validated alternatives."
    result_cards: list[dict]     # Formatted for frontend consumption
    export_text: str             # Flat text for copy-to-clipboard
    coverage_note: str | None
```

### TypeScript mirror (frontend/src/types/api.ts)
```typescript
export type Role = "researcher" | "pharma" | "ethics";
export type SourceType = "curated" | "llm_inferred";

export interface QueryRequest {
  input: string;
  role: Role;
}

export interface ResultCard {
  name: string;
  method_type: string;
  validation_status: string;
  description: string;
  source_url: string | null;
  citations: string[];
  source_type: SourceType;
  rationale?: string;  // only for llm_inferred
}

export interface FormattedResponse {
  role: Role;
  intent_summary: string;
  result_cards: ResultCard[];
  export_text: string;
  coverage_note: string | null;
}
```

---

## 2.10 Key Workflows

### Primary flow — query to results
```
User input + role selection
  → POST /query
  → Parser: extract ParsedIntent via Claude API
  → Retriever: vector search ChromaDB + fetch metadata from PostgreSQL
  → [if curated results < 3] Inferencer: Claude API gap-fill
  → Assembler: merge + rank + tag + coverage note
  → Formatter: shape output for selected role
  → FormattedResponse → frontend
```

### Data seeding flow (Phase 0, one-time)
```
ECVAM DB-ALM + NC3Rs website (manual extraction)
  → alternatives.json (hand-curated, ~25–40 entries)
  → Seed script: insert AnimalMethod + Alternative + join records → PostgreSQL
  → Embedding pipeline: generate embeddings for descriptions → ChromaDB
  → Smoke test: 5 hero queries return expected results
```

---

## 2.11 API Interface

| Endpoint | Method | Request | Response |
|---|---|---|---|
| `/query` | POST | `{input: string, role: string}` | `FormattedResponse` |
| `/health` | GET | — | `{status: "ok", db: bool, vector_db: bool}` |

**External API — Claude (Anthropic):**
- Called by Parser (intent extraction) and Inferencer (gap-filling)
- Prompt templates versioned in `/prompts/`
- Inferencer prompt instructs Claude to avoid fabricated citations; rationale field required

**ChromaDB abstraction:**
- All vector DB calls go through `db/vector_store.py`
- Interface: `search(query_embedding, n_results) → list[str]` (returns alternative IDs)
- Swap ChromaDB → Pinecone by replacing this file only; Retriever module unchanged

---

## 2.12 Development Dependencies

| Dependency | Type | Notes |
|---|---|---|
| Anthropic API key | Credential | Required before Phase 1 |
| Docker + Docker Compose | Tool | Dev environment |
| PostgreSQL (local) | Service | Via Docker |
| ChromaDB (local) | Service | Via Docker or embedded |
| Node 18+ | Runtime | Frontend |
| Python 3.11+ | Runtime | Backend |

---

## 2.13 MVP Definition

The MVP validates the core claim: **semantic input → credible, specific, citable alternatives.**

### MVP includes:
- Input panel with role selector and free-text input
- Full pipeline: Parser → Retriever → Inferencer → Assembler → Formatter
- PostgreSQL + ChromaDB populated from hand-curated seed dataset (~25–40 alternatives)
- Results display with source-type flagging (curated vs. inferred) — visually distinct
- At least one source link per curated result
- Coverage note displayed when inferencer activates
- Role-aware output framing for all three roles
- Copy-to-clipboard export

### MVP explicitly excludes:
- Regulatory jurisdiction metadata (label stub only: "Regulatory info — Full version")
- PDF export
- Saved searches or user accounts
- Confidence scores
- Access/cost information per alternative
- Automated data pipeline from ECVAM/NC3Rs exports

---

## 2.14 Roadmap

| Phase | Goal |
|---|---|
| **Phase 0** | Data pipeline: hand-curate seed dataset, populate PostgreSQL + ChromaDB |
| **Phase 1** | Core pipeline: Parser + Retriever + Inferencer + Assembler + Formatter (backend only) |
| **Phase 2** | Frontend: Input + Results panels wired to backend; role-aware formatting live |
| **Phase 3** | Polish + demo hardening: 5 hero queries bulletproof; coverage note UI; copy export |
| **Phase 4 (Full)** | Regulatory metadata, confidence scores, PDF export, user feedback loop |
| **Phase 5 (Full)** | Access/cost info, saved searches, improved ranking model |
| **Phase 6 (Extended)** | Institutional API, community contributions, grant platform integrations |

---

## 2.15 Hero Queries (locked for demo)

| Query | Expected output |
|---|---|
| "LD50 acute oral toxicity test in rats" | Curated: 3T3 NRU, H3D, cytotoxicity assays |
| "Skin sensitisation study using guinea pig maximisation test" | Curated: DPRA, KeratinoSens, h-CLAT |
| "Repeated dose 28-day systemic toxicity in mice" | Partial curated + inferencer; coverage note shown |
| "Eye irritation Draize test in rabbits" | Curated: EpiOcular, BCOP, STE |
| "Genotoxicity chromosomal aberration test" | Curated: in vitro micronucleus, Ames |

All 5 must return ≥ 3 results with correct source tagging and no 500 errors.

---

## 2.16 Critical Evaluation Notes

- **Most likely to be wrong at the halfway point:** Parser accuracy on vague or inconsistently written protocol descriptions. Mitigation: intent summary displayed to user before results — they can catch misinterpretation.
- **Greatest dependency risk:** ECVAM/NC3Rs data structure. Mitigated by hand-curation (ADR-004) — known format, known quality.
- **Is the MVP truly minimal?** Yes. Role-aware output is Minimal because it's load-bearing for the three-user-type value proposition. Removing it would break the core pitch.
- **ADR consistency check:** ADR-001 (hybrid data), ADR-002 (modular monolith + ChromaDB), ADR-003 (ECVAM/NC3Rs source), ADR-004 (hand-curation for hackathon) — all consistent with this spec as written.
