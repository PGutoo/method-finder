## Module 1 — Ideation

### 1.1 Starting Challenge

This challenge comes from Fórum Nacional de Proteção e Defesa Animal. 

💪 Challenge:The science world is still heavily reliant on animal testing not because there are no alternatives, but because researchers often don't know what those alternatives are or how to access them. That's a problem your team can help solve.

✨ Your opportunity: build a system that makes it easy for researchers to identify non-animal methods for any given study or test. Something that looks at an animal-based methodology and instantly surfaces credible, scientifically sound alternatives, making the ethical choice the obvious and easy one. If this works, it could accelerate the replacement of animal use in science in a way that decades of advocacy alone hasn't managed.

---

### 1.2 Problem Definition

**Surface problem:** Researchers use animal models even when alternatives exist.

**Root problem:** The knowledge gap is a friction problem, not an ethics problem. Most researchers aren't resistant to alternatives — they simply don't know what's available, whether it's validated, or how to access it. The ethical choice is harder than the default choice, so the default wins.

**Who experiences this:**
- **Academic researchers** designing studies, writing grants — face this at the methodology selection stage, often under time pressure
- **Pharma/biotech R&D teams** — need regulatory-accepted alternatives, not just theoretical ones
- **Ethics committee reviewers** — need to challenge animal use with credible alternatives, but lack the domain depth
- **Grant officers / funders** — increasingly required to justify animal use; need alternatives documented

**What the world looks like if solved:** A researcher designing a toxicity study can type in their methodology and get back a ranked list of validated in vitro, in silico, or organoid alternatives — with citations, validation status, regulatory acceptance, and access paths. The ethical choice becomes the path of least resistance.

**Reformulation:** Instead of "find alternatives to animal tests," reframe as "given a research question, what is the full menu of methods available to answer it?" — this is broader and more useful, because it doesn't assume the researcher is already committed to animal testing; it catches them earlier.

---

### 1.3 Solution Generation

Three distinct approaches, not variations:

**Approach A — The Search Engine Model**
A retrieval system: researcher inputs a methodology/test type, system queries a curated database of alternatives (3Rs databases, ECVAM, ICCVAM, published literature) and surfaces ranked results with metadata. Essentially a specialized search tool.

**Approach B — The AI Mapping Model**
An LLM-powered system that reads a researcher's protocol or abstract, understands the *biological question* being asked, and maps it to alternative methods — going beyond keyword matching to semantic understanding of what the experiment is trying to measure.

**Approach C — The Decision Support Model**
A guided workflow tool: researcher answers structured questions about their study goal, organism, endpoint, regulatory context → system generates a recommendation report with justification, ready to paste into a grant or ethics application.

**Combined approach worth considering:** A semantic input system (B+C) — the user describes their animal-based methodology in natural language or pastes a protocol; the system understands the biological question being asked, maps it to validated non-animal alternatives (from academic literature), and returns structured output usable directly in grant applications, ethics submissions, or R&D documentation.

---

### 1.4 Market & Value Check

Target users (all three):
* Academic researchers — at methodology selection / grant writing stage, designing a study involving toxicology, pharmacology, disease modeling, or safety testing.
* Pharma / biotech R&D — needing regulatory-accepted alternatives with jurisdiction metadata
* Ethics committee reviewers — needing to challenge animal use proposals with credible alternatives

**Core value proposition:** Reduce the time and expertise required to identify credible, validated, citable alternatives from "weeks of literature review" to "minutes."

**Key differentiators vs. existing solutions:**
- **ECVAM / EURL databases** exist but are hard to query, not semantic, not user-friendly
- **NC3Rs website** has guidance but isn't interactive or specific to your protocol
- **General AI tools** hallucinate citations and don't know regulatory validation status
- This system's edge: validated data + semantic input parsing + output formatted for actual use (grant language, not academic jargon)

**Biggest gap current solutions leave:** None of them take *your specific protocol* as input. They're all general directories. That's the whitespace.

---

### 1.5 Scope Definition

| Tier | Description |
|---|---|
| **Minimal** | Input: free-text description of animal-based method. Output: list of validated alternatives with source links, basic metadata (validation status, species replaced, endpoint type) |
| **Full** | Semantic protocol parsing + ranked alternatives + regulatory acceptance status + access/cost info + output formatted for ethics applications |
| **Extended** | Full + researcher profiles, saved searches, integration with grant platforms, community-contributed method updates, API for institutions |

**My recommendation: start at Minimal, but design with Full in mind.** The core value (semantic input → credible alternatives) needs to be proven before the output formatting and regulatory metadata are worth building. The data sourcing strategy is the real risk to validate first.

Scope tier: Minimal — but every design decision made at this stage must be compatible with Full. Nothing built now should need to be torn down to add regulatory metadata, role-specific output formats, or richer data sourcing later.
Rationale: The core value (semantic input → credible, citable alternatives) is unproven and data-dependent. Prove that first. The output formatting and regulatory layers are valuable — but only if the matching quality earns researcher trust.

---

### 1.6 — Assumption Stress-Test
Before we commit to a spec, let's pressure-test the four things that could kill this silently.

Riskiest assumption — and how to test it cheaply:
The single assumption that kills this project if wrong: "The system can match a described methodology to relevant alternatives with enough specificity to be useful."
A general match ("here are some in vitro options") has zero value to a researcher running a specific assay. The system needs to distinguish between, say, a repeated-dose oral toxicity study and a skin sensitization test — and return different, specific alternatives for each.
Cheap test: Before building anything, manually take 5–10 real animal-based protocols from published papers and try to find their validated alternatives using existing sources (ECVAM, NC3Rs, literature). If you can't do it manually with domain knowledge, the system can't do it automatically without a very strong data layer. This tells you whether the data exists and whether the matching problem is tractable.

Personal fit check — flag this explicitly:
Three questions you need to answer honestly before proceeding:

Do you have access to someone with domain expertise in 3Rs / alternative methods — or a way to validate the system's outputs? (If no, output quality is unverifiable and trust is unearnable.)
Is this being built for a specific competition/deadline, or as a longer-term product? (This changes what "done" means.)
Is the team comfortable working with scientific literature data, licensing constraints, and database curation? (The data layer is not a side concern — it's the product.)


Technical feasibility flags — carry these into the spec as explicit constraints:
FlagRisk levelNotesData sourcing🔴 HighWhere does the alternatives database come from? ECVAM/EURL data is structured but limited. Broader coverage requires literature parsing or manual curation — neither is trivial.Semantic matching quality🟡 MediumLLMs can parse methodology descriptions well, but hallucinating alternatives is a serious trust risk. Retrieval-Augmented Generation (RAG) over a curated dataset is the safer architecture than pure generation.Regulatory metadata🟡 MediumJurisdiction-specific validation status (OECD, FDA, EMA) is valuable but complex. Can be stubbed for Minimal if clearly flagged as incomplete.Multi-user output formatting🟢 LowRole-aware output templates are straightforward once the core matching works.

Success definition — one sentence, observable, binary:

A researcher can paste or describe an animal-based methodology and receive at least 3 validated, citable, non-animal alternatives that a domain expert confirms are relevant and specific to that methodology.


Go / No-go:
This is a conditional Go. The concept is sound and the need is real. The condition: the data sourcing strategy must be defined before the spec is finalized — it's the load-bearing wall of the whole system. If the data layer is "we'll use an LLM and hope," that's a No-go. If the data layer is "RAG over curated sources + explicit coverage limits," that's a Go.
Risks carried forward into the spec:

🔴 Data sourcing strategy must be a first-class spec decision, not a footnote
🟡 Matching specificity must be testable — acceptance criteria need to include domain-expert validation
🟡 Hallucination risk must be architecturally mitigated (RAG, not pure generation)
Output must clearly communicate confidence level and coverage gaps to the user — silence about what the system doesn't know is a trust killer

---

### 1.7 Critical Evaluation — Steelman the Objections

**Three strongest reasons this fails:**

1. **Data quality problem.** The value of this tool lives entirely in the quality and currency of its alternatives database. If it surfaces outdated, unvalidated, or poorly-matched alternatives, researchers will distrust it fast — and in science, lost trust is permanent. Building and maintaining that data layer is much harder than building the interface.

2. **Specificity trap.** A researcher running a *specific* neurotoxicity assay on a *specific* compound class needs very targeted alternatives. A general "here are some in vitro options" output is useless to them. The tool has to be specific enough to be actionable, which requires deep domain coverage — hard to achieve broadly.

3. **Regulatory legitimacy gap.** In pharma and safety testing, "alternative exists" is not enough — the alternative must be *regulatory-accepted* in the relevant jurisdiction. If the tool doesn't clearly flag this, it could actively mislead researchers who then propose alternatives that get rejected. That's worse than not using the tool.

**What could be assumed that's wrong:**
- That researchers are the right entry point — ethics committees or funders might be higher-leverage
- That the bottleneck is *discovery* — it might actually be *validation status uncertainty* or *implementation support*

**Simpler version that achieves the same goal:** A well-curated, searchable database with good tagging — no AI, no semantic parsing. Less impressive, but possibly more trusted and easier to keep accurate.
