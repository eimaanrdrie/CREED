# CREED

**Reversible Self-Learning Delivery Assurance for Software Transformation**

Prototype baseline: **R94.0.6 / UI R99-M06**  
Backend API: **0.94.6**

CREED is a **local-first, human-governed, Glass Box assurance prototype** for software delivery and transformation work.

- **Agentic AI**  
  Orchestrates the multi-stage delivery assurance workflow from issue intake through investigation, Human Decision, learning, adoption and recall.

- **Local GEN AI**  
  Uses Qwen models running locally through Ollama for issue understanding, evidence-backed investigation and governed self-learning.

- **Evidence-Backed Analysis**  
  Retrieves governed evidence, identifies affected client implementations and analyses each candidate using its own supporting evidence.

- **Human-in-Control**  
  Pauses for Human Decision before governed outcomes are recorded or reusable knowledge is approved.

- **Governed Self-Learning**  
  Converts approved Human Corrections into reusable knowledge that can be versioned and adopted.

- **Scoped Adoption**  
  Controls exactly where approved knowledge may be reused instead of automatically applying it everywhere.

- **Reversible Learning**  
  Approved knowledge can later be recalled when new evidence invalidates it.

- **Glass Box Audit**  
  Keeps AI outputs, evidence, original sources, A-BOM relationships, Human Decisions, approvals, adoption scope and recall records traceable throughout the workflow.

> **Correct forward. Recall backward. Learn reversibly.**

> The bundled dataset is synthetic demo data, not production client data.

---

## Workflow

CREED uses a **Glass Box audit workflow**. Each stage keeps the evidence, system relationships, AI execution and human governance records visible and traceable.

```text
Live Issue
   ↓
Qwen Understanding
   ↓
Evidence Repository
   ↓
A-BOM / Registry Resolution
   ↓
Candidate Investigation
   ↓
Human Decision
   ↓
Learning & Adoption
   ↓
Approved Knowledge
   ↓
Explicit Adoption
   ↓
Knowledge Recall
```

| Workflow Stage | What Happens | Glass Box Audit Trace |
|---|---|---|
| **Issue** | User submits a live delivery or support issue | Original issue, client, ticket, type, severity and observation are preserved |
| **Qwen Understanding** | Local GenAI structures the issue for retrieval and routing | Model, runtime status and generated interpretation remain visible |
| **Evidence Repository** | CREED retrieves governed source material | Source title, excerpt, retrieval match, original file preview and SHA-256 verification are available |
| **A-BOM / Registry Resolution** | CREED identifies which implementations use the relevant Method Version | Implementation, Method Version, Dependency and supporting evidence relationships are traceable |
| **Investigation** | Each candidate implementation is analysed against its own evidence | Current state, requested state, technical result, AI analysis and source evidence are expandable |
| **Human Decision** | Authorized reviewer makes the governed outcome | Reviewer, decision, rationale and authority are persisted |
| **Learning & Adoption** | CREED performs human-governed self-learning by converting an approved Human Correction into reusable knowledge that can be versioned and adopted | Human correction, Qwen learning proposal, Learning Authority, rationale, adoption scope and approval state are recorded |
| **Approved Knowledge** | Approved reusable Method Versions are made visible | Approved version, authority, adoption scope, receipt and in-use relationships can be inspected |
| **Explicit Adoption** | An implementation is explicitly linked to an approved Method Version | Dependency registration proves which implementation actually uses the approved version |
| **Knowledge Recall** | Approved knowledge can be recalled when new evidence invalidates it | Recall authority, reason, routed implementations, exclusions and Signed Recall Notice are preserved |
| **Glass Box Audit** | Makes the full decision path inspectable end to end | AI conclusion -> evidence -> original source -> A-BOM relationship -> Human Decision -> governed approval or recall receipt |

---

## Setup and Run

Use Docker Compose for the simplest full prototype setup.

### 1. Install prerequisites

| Requirement | Purpose |
|---|---|
| Docker Desktop / Docker Compose | Runs PostgreSQL, backend and frontend |
| Ollama | Runs the local Qwen models |
| 12 to 16 GB RAM recommended | Local GenAI demo |

### 2. Install and start the Qwen models

Run once:

```bash
ollama pull qwen3.5:9b
ollama pull qwen3.5:4b
ollama pull qwen3-embedding:0.6b
```

Start Ollama:

```bash
ollama serve
```

Keep Ollama running while using CREED.

### 3. Configure the demo environment

Backend settings are defined in `backend/.env.example`.

For the live demo, ensure:

```env
DATABASE_URL=postgresql+psycopg://creed:creed@postgres:5432/creed

OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3.5:9b
OLLAMA_RUNTIME_MODEL=qwen3.5:4b
OLLAMA_INVESTIGATION_MODEL=qwen3.5:4b
OLLAMA_LEARNING_MODEL=qwen3.5:4b

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:0.6b

DOCUMENT_STORAGE_PATH=.data/documents
LANGGRAPH_CHECKPOINT_PATH=.data/langgraph-checkpoints.sqlite

DEMO_MODE_ENABLED=true
```

Frontend:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`DEMO_MODE_ENABLED=true` is intended for judging or rehearsal only. Keep it disabled in a normal environment.

### 4. Start CREED

From the repository root:

```bash
docker compose up --build
```

Wait until the services are running.

| Service | URL |
|---|---|
| CREED UI | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Demo readiness | http://localhost:3000/demo |

Docker keeps prototype data in persistent volumes:

| Volume | Purpose |
|---|---|
| `creed_postgres` | PostgreSQL data |
| `creed_documents` | Original evidence files |
| `creed_langgraph` | LangGraph checkpoints |

### 5. Prepare the live demo

Open the operator-only demo readiness route:

```text
http://localhost:3000/demo
```

Then:

1. Click **Reset synthetic baseline**
2. Confirm the reset
3. Click **Refresh readiness**
4. Wait for **READY TO START**
5. Click **Start live issue**

Expected clean baseline:

| Item | Expected |
|---|---:|
| Clients / Implementations | 3 / 3 |
| Indexed evidence documents | 10 indexed |
| A-BOM and evidence relationships | 11 |
| Active Human Authorities | 5 |
| Production deployments | 3 |
| Ownership assignments | 10 |
| Active live issue / Human Decisions | 0 / 0 |
| Active learning / recalls | 0 / 0 |

### 6. Run the live workflow

```text
Create Issue
  ↓
Save & analyse
  ↓
Evidence Retrieval
  ↓
Investigation
  ↓
Human Decision
  ↓
Learning & Adoption
  ↓
Approved Knowledge
  ↓
Optional Knowledge Recall
```

CREED should perform Qwen inference, evidence retrieval, candidate routing, investigation, runtime logging, Human Decision gating, learning proposal generation, adoption receipt creation and recall routing from live execution.

### 7. Stop or reset the environment

Stop CREED:

```bash
docker compose down
```

Start it again later:

```bash
docker compose up
```

Remove all persistent prototype data:

```bash
docker compose down -v
```

Use `down -v` only when you intentionally want a completely clean environment.
---

## Technology Stack

| Layer | Technology | Used For |
|---|---|---|
| **Frontend** | Next.js 16.3.1 | Application routing and SSR |
|  | React 19 | Interactive UI |
|  | TypeScript 5.7 | Type-safe frontend code |
|  | Tailwind CSS 4 | Styling |
|  | Lucide React | Icons |
| **Backend** | Python 3.12 | Backend runtime |
|  | FastAPI 0.128.2 | REST API |
|  | Uvicorn 0.48.0 | ASGI server |
|  | Pydantic 2.13.4 | Validation and settings |
|  | SQLAlchemy 2.0.50 | ORM and persistence |
|  | Alembic 1.18.4 | Database migrations |
| **Agentic AI** | LangGraph 1.2.11 | Multi-stage workflow orchestration |
|  | LangGraph SQLite Checkpointer | Workflow checkpoints |
| **Local GEN AI** | Ollama | Local model serving |
|  | Qwen 3.5 9B | Issue understanding |
|  | Qwen 3.5 4B | Investigation, runtime and learning |
|  | Qwen Embedding 0.6B | Local embeddings |
| **Data** | PostgreSQL 17 | Core application data |
|  | pgvector | Vector retrieval |
|  | psycopg 3.x | PostgreSQL driver |
| **Documents** | pypdf | PDF text extraction |
|  | python-docx | DOCX extraction |
|  | python-multipart | File uploads |
| **Testing** | pytest | Backend and regression tests |

---

## Agentic AI and Local GEN AI

CREED combines **Agentic AI** for workflow orchestration with **Local GEN AI** for reasoning and knowledge generation.

| AI Layer | Technology | Role in CREED |
|---|---|---|
| **Agentic AI** | LangGraph | Orchestrates the multi-stage workflow from issue intake through retrieval, impact analysis, investigation, Human Decision and governed handoff |
| **Local GEN AI** | Ollama + Qwen 3.5 9B | Interprets the live issue and structures it for retrieval and routing |
| **Local GEN AI** | Ollama + Qwen 3.5 4B | Performs candidate investigation, runtime analysis and generates governed learning proposals |
| **Local Embeddings** | Qwen Embedding 0.6B | Creates embeddings for evidence retrieval through pgvector |
| **Human Governance** | Human Authority controls | Makes final impact decisions, approves reusable learning and authorizes recall |

### How Agentic AI works

LangGraph coordinates CREED as a sequence of governed tasks rather than a single chatbot response.

```text
Issue Intake
   ↓
Evidence Retrieval
   ↓
Knowledge / A-BOM Linking
   ↓
Impact Routing
   ↓
Candidate Investigation
   ↓
Evidence Validation
   ↓
Human Decision
   ↓
Learning & Adoption
```

Each stage has a specific responsibility, runtime state and output that can be inspected in the Glass Box workflow.

### How Local GEN AI works

Qwen models run locally through Ollama. CREED uses them for tasks that require language understanding and structured reasoning, while governed evidence, Registry relationships and Human Authority remain the control boundaries.

```text
Live issue
   ↓
Local Qwen understanding
   ↓
Evidence-backed analysis
   ↓
Human-approved correction
   ↓
Qwen learning proposal
   ↓
Reusable approved knowledge
```

This keeps the GenAI workflow local-first while preserving evidence traceability and human control.

---

## Architecture

```text
                    ┌─────────────────────┐
                    │   Next.js Frontend  │
                    │  React + TypeScript │
                    └──────────┬──────────┘
                               │ HTTP / JSON
                               ▼
┌───────────────┐     ┌────────┴────────┐     ┌──────────────────────┐
│    Ollama     │◄───►│ FastAPI Backend │◄───►│ PostgreSQL + pgvector│
│  Local Qwen   │     │ + LangGraph     │     │ Data + Retrieval     │
└───────────────┘     └────────┬────────┘     └──────────────────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
         Governed document storage   Workflow checkpoints
```

### Key Architectural Notes

| Principle | How CREED applies it |
|---|---|
| **Evidence-first** | AI conclusions are grounded in persisted evidence and Registry relationships |
| **Human-in-control** | Humans make final decisions, approve learning and authorize recall |
| **Approval is not deployment** | Approved knowledge does not automatically change client implementations |
| **Scoped learning** | Adoption scope controls where approved knowledge may be reused |
| **Reversible learning** | Approved knowledge can later be recalled using governed evidence |
| **Fail closed** | Missing or conflicting evidence returns reconciliation states instead of AI guesses |
| **Source integrity** | Original files are served only after SHA-256 verification |

---

## A-BOM and Registry Model

CREED uses a local dependency and evidence map to answer:

> **Which implementation uses which method version, and what evidence proves it?**

```text
Atlas Bank
   ↓
Atlas PTP Implementation R1
   ↓ uses
PTP-EVENT-v1
   ↓ supported by
CFG-ATLAS-PTP-01
```

| Registry Item | Meaning |
|---|---|
| **Product** | Top-level software product |
| **Module** | Functional area within a product |
| **Client** | Customer organisation |
| **Implementation** | Client-specific setup of a module |
| **Method** | Reusable delivery approach and versions |
| **Dependency** | Link showing which implementation uses which Method Version |
| **Deployment** | Where and when an implementation release was promoted |

### Method vs Approved Knowledge

| Method | Approved Knowledge |
|---|---|
| Technical catalog of reusable approaches and versions | Governed view of versions approved for reuse |
| Can contain Draft, Proposed, Approved or Recalled versions | Shows approved knowledge with authority, rationale, scope and receipt |
| Managed under Registry | Visible as a main navigation area |

A new Method Version is created only when reusable knowledge for the same method meaningfully changes, not for every issue.

---

## Evidence Repository

Original source files and extracted or indexed text are stored separately.

| File Type | Preview Behaviour |
|---|---|
| PDF | Original PDF rendered inline |
| Markdown / TXT / JSON | SHA-256 verified original text |
| DOCX | Original file retained, extracted text available for retrieval |

Document storage is anchored to the backend storage directory so files remain addressable after backend restarts.

---

## Testing

| Test | Command |
|---|---|
| Release integration | `python scripts/verify_r94_0_6_m08.py` |
| Current UI verifier | `python scripts/verify_ui_r99_m03.py` |
| Backend tests | `PYTHONPATH=. pytest -q` |
| Frontend lint | `npm run lint` |
| Frontend production build | `npm run build` |

Windows PowerShell backend tests:

```powershell
$env:PYTHONPATH="."
pytest -q
```

---

## Repository Structure

```text
creed-mvp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── domain/
│   │   ├── repositories/
│   │   └── services/
│   ├── demo_data/
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   └── package.json
├── scripts/
├── docker-compose.yml
└── README.md
```
