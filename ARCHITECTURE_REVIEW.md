# Architecture Review: Enterprise AI Assistant
> Analysis date: 2026-09-29  
> Reviewer: Senior AI/ML Architect + SDET perspective  
> Status: READ-ONLY analysis — no source code was modified

---

## ⚠️ Critical Discrepancies Found (README vs. Code)

Before anything else, these must be known:

| README claims | What the code actually does |
|---|---|
| Chroma Vector Store | **FAISS** (`faiss-cpu`) — `vectorstore.py` line 1 |
| CI/CD & GitHub Actions | **No `.github/` directory exists** — zero workflows |
| DOC/DOCX support | **Only PDF and TXT loaders** are implemented in `loader.py` |
| `.env.example` file | **Does not exist** in the repository |
| "Enterprise" AI | Single-process, in-memory, no auth, no persistence |

---

## Executive Summary

This is a **full-stack RAG (Retrieval-Augmented Generation) application** that lets a user upload a document, ask natural-language questions about it, and receive answers grounded in that document's content. The system consists of:

- A **React/Vite frontend** for chat and file upload
- A **FastAPI backend** implementing the RAG pipeline and a query router
- **FAISS** as an in-memory vector store
- **HuggingFace sentence-transformers** for embeddings (`all-mpnet-base-v2`)
- **Ollama + llama3.2** as the local LLM (running on the host, outside Docker)
- **Docker Compose** for local development orchestration

The project is a solid working prototype with significant gaps: no persistence, no tests, no CI/CD, no chunking strategy, and no evaluation framework. Its strengths are a clean architecture, real RAG wiring, and a working Dockerized development environment.

---

## Technology Stack

### Backend
| Component | Library/Tool | Version |
|---|---|---|
| Web framework | FastAPI | unpinned |
| ASGI server | Uvicorn | unpinned |
| LLM orchestration | LangChain | unpinned |
| LLM provider | Ollama (`langchain-community`) | llama3.2 |
| Embedding model | HuggingFace `sentence-transformers/all-mpnet-base-v2` | unpinned |
| Vector store | FAISS (`faiss-cpu`) | unpinned |
| PDF loading | PyPDF (`pypdf`) | unpinned |
| File upload | `python-multipart` | unpinned |
| Prompt abstraction | `langchain-core` PromptTemplate | unpinned |

### Frontend
| Component | Library/Tool | Version |
|---|---|---|
| UI framework | React | ^18.2.0 |
| Build tool | Vite | ^5.0.8 |
| Styling | Tailwind CSS | ^3.3.6 |
| HTTP client | Native `fetch` | — |

### Infrastructure
| Component | Tool |
|---|---|
| Containerization | Docker (python:3.11-slim + node:18-alpine) |
| Orchestration | Docker Compose v3.8 |
| Production web server | Nginx (alpine) — `Dockerfile.prod` only |
| LLM host | Ollama on host machine (not containerized) |

### Missing
- No CI/CD (no `.github/`, no pipelines)
- No tests (no test files anywhere)
- No database (PostgreSQL, MongoDB, etc.)
- No authentication layer
- No rate limiting
- No logging framework
- No monitoring / observability

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              React UI  (Vite dev server :5173)           │   │
│  │   ChatWindow.jsx                                         │   │
│  │   ├── chat()          → POST /chat/                      │   │
│  │   └── uploadDocument() → POST /ingest/                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP (JSON / multipart)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend  (:8000)                       │
│                    app/main.py                                    │
│                                                                  │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ /health/   │  │  /ingest/    │  │       /chat/            │  │
│  │ health.py  │  │  ingest.py   │  │       chat.py           │  │
│  └────────────┘  └──────┬───────┘  └──────────┬─────────────┘  │
│                         │                      │                 │
│                         ▼                      ▼                 │
│                 ┌───────────────┐    ┌─────────────────────┐   │
│                 │ DocumentLoader│    │  Task Router         │   │
│                 │ loader.py     │    │  task_router.py      │   │
│                 │               │    │  (LLM prompt →       │   │
│                 │ PyPDFLoader   │    │   RAG/SUMMARIZE/      │   │
│                 │ TextLoader    │    │   WORKFLOW)           │   │
│                 └──────┬────────┘    └──────────┬───────────┘   │
│                        │                        │               │
│                        ▼                        │               │
│                 ┌──────────────┐                │               │
│                 │  VectorDB    │◄───────────────┤               │
│                 │  vectorstore │  search(query) │               │
│                 │  .py         │                │               │
│                 │              │                │               │
│                 │  FAISS index │                │               │
│                 │  (in-memory) │                │               │
│                 └──────┬───────┘                │               │
│                        │                        │               │
│                        ▼                        │               │
│                 ┌──────────────┐                │               │
│                 │  Embedder    │                │               │
│                 │  embedder.py │                │               │
│                 │              │                │               │
│                 │  HuggingFace │                │               │
│                 │  all-mpnet-  │                │               │
│                 │  base-v2     │                │               │
│                 └──────────────┘                │               │
│                                                 │               │
└─────────────────────────────────────────────────│───────────────┘
                                                  │ HTTP
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Ollama  (host machine :11434)                    │
│                 Model: llama3.2                                  │
│  Used for:                                                       │
│  1. Route classification (RAG/SUMMARIZE/WORKFLOW)                │
│  2. Grounded answer generation (RAG path)                        │
│  3. Open-ended summarization (SUMMARIZE path)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Diagrams

### A. Document Ingestion Flow

```
User clicks "Upload Document" (ChatWindow.jsx:22)
  │
  ▼
uploadDocument(file)  [api.js:12]
  │  POST /ingest/   multipart/form-data
  ▼
ingest(file: UploadFile)  [ingest.py:11]
  │
  ├─ Write file to OS temp dir  (tempfile.NamedTemporaryFile)
  │
  ▼
DocumentLoader.load(tmp_path)  [loader.py:6]
  │
  ├─ .pdf  → PyPDFLoader(path).load()   [returns List[Document]]
  └─ other → TextLoader(path).load()    [returns List[Document]]
       │
       │  ⚠️  NO TEXT SPLITTING  — documents ingested as whole pages (PDF)
       │      or whole file (TXT). PyPDFLoader returns one Document per page.
       ▼
vectordb.build(docs)  [vectorstore.py:9]
  │
  └─ FAISS.from_documents(docs, embedder)
       │
       ├─ embedder = HuggingFaceEmbeddings("all-mpnet-base-v2")  [embedder.py:3]
       │   Converts each doc's page_content → 768-dim float vector
       │
       └─ Builds in-memory FAISS index (L2/cosine)
            │
            └─ Stored as self.db on the VectorDB singleton
               ⚠️  REPLACES previous index on every upload
               ⚠️  LOST on container restart

  Response: {"status": "indexed", "chunks": len(docs)}
```

### B. Chat / Query Flow

```
User types question, presses Enter  (ChatWindow.jsx:11)
  │
  ▼
chat(input)  [api.js:3]
  │  POST /chat/  {"query": "..."}
  ▼
chat(req: ChatRequest)  [chat.py:19]
  │
  ├─ STEP 1: Route classification
  │   llm.invoke(router_prompt.format(query=req.query))
  │   → Ollama (llama3.2) classifies query as "RAG", "SUMMARIZE", or "WORKFLOW"
  │   → Expected response: single label string (strip() applied)
  │
  ├─ route == "RAG"
  │   ├─ Guard: if vectordb.db is None → error response
  │   ├─ vectordb.search(req.query)   [vectorstore.py:12]
  │   │   → embedder.embed_query(query)  → 768-dim vector
  │   │   → FAISS.similarity_search(query, k=5)
  │   │   → Returns top-5 Document objects
  │   │
  │   ├─ context = "\n".join([d.page_content for d in docs])
  │   │   ⚠️  No metadata, no source attribution, no deduplication
  │   │
  │   └─ llm.invoke(f"Context: {context}\nQuestion: {req.query}")
  │       → Ollama generates grounded answer
  │       → {"route": "RAG", "answer": <string>}
  │
  ├─ route == "SUMMARIZE"
  │   └─ llm.invoke(f"Summarize: {req.query}")
  │       → Direct LLM call, no document context
  │       → {"route": "SUMMARIZE", "answer": <string>}
  │
  └─ else (WORKFLOW or unexpected)
      → {"route": "WORKFLOW", "answer": "Workflow execution coming soon."}
```

---

## Component Analysis

### 1. `backend/app/main.py` — Application Bootstrap

**CONFIRMED FROM CODE**

- Creates FastAPI instance
- Registers CORS middleware — `allow_origins=["http://localhost:5173"]` (hardcoded, single origin)
- Mounts three routers: `/chat`, `/ingest`, `/health`
- No lifespan hooks, no startup event handlers
- The `vectordb` singleton and `llm` instance are created at **import time** when the module loads

**Critical weakness:** CORS is hardcoded to localhost:5173. Any production deployment would silently fail cross-origin requests.

---

### 2. `backend/app/api/chat.py` — Chat Endpoint

**CONFIRMED FROM CODE**

- Module-level initialization: `llm = Ollama(model="llama3.2", base_url=ollama_host)` — this connection is created once when the module first imports
- `ollama_host` reads from `OLLAMA_HOST` env var, defaulting to `http://localhost:11434`
- The router classification is a **separate LLM call** before the RAG call — this means every RAG query consumes **two Ollama round-trips**
- The routing prompt (`task_router.py`) asks the LLM to return exactly one label. There is no fallback for hallucinated/unexpected output — if LLM returns "I think this is RAG" instead of "RAG", it falls through to WORKFLOW silently
- RAG prompt is a raw f-string, not a LangChain PromptTemplate — no structure, no validation

**Potential failure modes:**
- `vectordb.db is None` → handled with guard (line 25)
- LLM returns unexpected route label → silently goes to WORKFLOW (no error logged)
- Ollama not running → `Exception` caught, returns error string (no status code differentiation)
- Context window overflow (very large documents) → no truncation logic

---

### 3. `backend/app/api/ingest.py` — Document Ingestion Endpoint

**CONFIRMED FROM CODE**

- Accepts any `UploadFile` — no MIME type validation, no file size limit
- Writes to `tempfile.NamedTemporaryFile` with correct suffix (preserves extension for loader routing)
- `os.unlink(tmp_path)` in `finally` block — good, prevents temp file leak
- Calls `vectordb.build(docs)` which **replaces** the entire FAISS index on each upload
- Returns `len(docs)` as "chunks" — this is actually document count (pages for PDF), not text chunks

**Critical weakness:** Every new upload destroys the previous index. You cannot build a knowledge base from multiple documents — the second document upload erases the first.

---

### 4. `backend/app/rag/loader.py` — Document Loader

**CONFIRMED FROM CODE**

- `DocumentLoader.load(path)` — static method, routes by file extension
- `.pdf` → `PyPDFLoader(path).load()` — returns one `Document` per PDF page
- anything else → `TextLoader(path).load()` — returns the entire file as one `Document`
- No `.doc`/`.docx` support despite UI accepting these MIME types
- No text splitting / chunking — documents ingested as raw pages or full files

**Why this matters architecturally:** Without chunking, you're searching against full PDF pages (potentially 500-1000 tokens each). This degrades retrieval quality for long documents because:
1. The vector represents the entire page, not a focused concept
2. Top-K returns pages, not semantically focused passages
3. Context window may overflow with 5 full pages

---

### 5. `backend/app/rag/embedder.py` — Embedding Model

**CONFIRMED FROM CODE**

```python
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
```

- Module-level singleton — created once at import time
- Model: `all-mpnet-base-v2` — 768-dimensional embeddings, MPNet architecture
- Downloads from HuggingFace Hub on first run (cached in `~/.cache/huggingface`)
- In Docker: `backend-cache:/root/.cache` volume persists the model between container restarts
- Symmetric model (document and query use same embedding space — correct for FAISS similarity_search)

**Technical details of all-mpnet-base-v2:**
- 768-dim output vectors
- ~110M parameters
- Strong general-purpose sentence similarity
- Not domain-specific (may underperform on highly technical enterprise documents)
- Max input tokens: 512 (documents longer than ~380 words will be truncated silently)

---

### 6. `backend/app/rag/vectorstore.py` — FAISS Vector Store

**CONFIRMED FROM CODE**

```python
class VectorDB:
    def __init__(self):
        self.db = None
    def build(self, docs):
        self.db = FAISS.from_documents(docs, embedder)
    def search(self, query):
        return self.db.similarity_search(query, k=5)

vectordb = VectorDB()
```

- Module-level singleton: `vectordb = VectorDB()`
- `build()` replaces the entire index — no incremental adding
- `search()` uses `similarity_search(query, k=5)` — top-5 results
- FAISS `similarity_search` via LangChain uses **cosine similarity** by default (L2 on normalized vectors)
- `self.db = None` on startup — guarded in `chat.py`
- **In-memory only** — no `save_local()` / `load_local()` calls — index lost on restart

---

### 7. `backend/app/agents/task_router.py` — Query Router

**CONFIRMED FROM CODE**

```python
router_prompt = PromptTemplate.from_template("""
You are a routing agent. Classify the user request into one of:
- RAG
- SUMMARIZE
- WORKFLOW
Return only the label.
Query: {query}
""")
```

- Uses `PromptTemplate.from_template` — LangChain v0.1+ style
- Prompt instructs LLM to return exactly one label
- No few-shot examples — routing quality depends entirely on llama3.2's instruction following
- No output parsing / validation — `.strip()` is the only normalization applied
- WORKFLOW route is a dead stub

**Architectural observation:** Using an LLM to route queries is expensive — doubles inference latency. Rule-based routing (keyword matching) or a lightweight classifier would be faster and more deterministic.

---

### 8. `ui/src/components/ChatWindow.jsx` — Chat UI

**CONFIRMED FROM CODE**

- Manages three pieces of state: `input`, `messages`, `uploading`
- Messages stored as `{q, a}` pairs in component state — **lost on page refresh**
- No loading indicator for chat (only for uploads)
- No error display in the chat window — errors shown via `alert()` (poor UX)
- File input `accept=".pdf,.txt,.doc,.docx"` — .doc and .docx are not supported by backend
- No streaming — waits for full response before displaying
- `onKeyPress` (deprecated API) instead of `onKeyDown`

---

## Docker Architecture

### Development Setup (docker-compose.yml)

```
┌─────────────────────────────────────────────────────┐
│  Docker Compose Network                             │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  backend service                              │  │
│  │  Image: python:3.11-slim                      │  │
│  │  Port: 8000:8000                              │  │
│  │  Env: OLLAMA_HOST=http://host.docker.internal:11434 │
│  │  Volume: ./backend:/app  (hot reload)         │  │
│  │  Volume: backend-cache:/root/.cache (models)  │  │
│  │  Healthcheck: GET /health/ every 30s          │  │
│  │  CMD: uvicorn --reload                        │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  frontend service                             │  │
│  │  Image: node:18-alpine                        │  │
│  │  Port: 5173:5173                              │  │
│  │  Env: VITE_API_URL=http://localhost:8000      │  │
│  │  Volume: ./ui:/app  (HMR)                     │  │
│  │  depends_on: backend                          │  │
│  │  CMD: npm run dev -- --host 0.0.0.0           │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
└────────────────────────────┬────────────────────────┘
                             │ host.docker.internal
                             ▼
┌─────────────────────────────────────────────────────┐
│  HOST MACHINE                                       │
│  Ollama :11434  (NOT containerized)                 │
└─────────────────────────────────────────────────────┘
```

### Production Setup (Dockerfile.prod — ui only)

The production Dockerfile for the frontend is a proper multi-stage build:
1. **Stage 1 (builder):** `node:18-alpine` → `npm ci` → `npm run build` → creates `/app/dist`
2. **Stage 2 (runtime):** `nginx:alpine` → copies `dist/` → serves on port 80

The nginx config:
- Serves React as SPA (all routes → `index.html`)
- Proxies `/api` → `http://backend:8000` (requires both services on same Docker network)
- 1-year cache headers on static assets

**Docker anti-patterns found:**

| Issue | Location | Impact |
|---|---|---|
| `--reload` in production CMD | `backend/Dockerfile:21` | Watches filesystem in prod, wastes resources, can cause instability |
| Unpinned requirements | `requirements.txt` | Non-reproducible builds — `faiss-cpu` version could change between builds |
| No multi-stage build for backend | `backend/Dockerfile` | Dev tools and build artifacts included in production image |
| No `.env` file (referenced in docs) | root | Configuration is manual or missing |
| FAISS index not persisted to volume | `vectorstore.py` | Data lost on every restart |
| `VITE_API_URL=http://localhost:8000` in compose | `docker-compose.yml` | Frontend calls backend directly from browser, bypassing the nginx proxy path |

---

## CI/CD Architecture

**CONFIRMED FROM CODE: There is NO CI/CD.**

The repository has:
- One git commit (`initial-commit`)
- No `.github/` directory
- No GitHub Actions workflows
- No other CI configuration (no CircleCI, Jenkins, etc.)

The README mentions "CI/CD" as a feature — this is aspirational, not implemented.

What CI/CD **should** do for this project (and doesn't):
```
Developer pushes code
  ↓
GitHub Actions trigger
  ↓
┌─────────────────────────────────────┐
│  CI Pipeline (MISSING)              │
│  ├── Install Python deps            │
│  ├── Run pytest (NO TESTS EXIST)    │
│  ├── Lint (flake8/ruff)             │
│  ├── docker build backend           │
│  ├── docker build frontend          │
│  ├── Integration test               │
│  └── PASS / FAIL                    │
└─────────────────────────────────────┘
```

---

## Testing Architecture

**CONFIRMED FROM CODE: There are NO tests.**

```
find . -name "test_*" → 0 results
find . -name "*_test.py" → 0 results
find . -name "pytest.ini" → 0 results
```

### What should be tested (and isn't)

| Test Type | What to Test | Priority |
|---|---|---|
| Unit | `DocumentLoader.load()` routing logic | P0 |
| Unit | `VectorDB.build()` / `search()` behavior | P0 |
| Unit | Router prompt → expected labels | P0 |
| Unit | `chat()` route branch logic | P0 |
| Integration | Ingest → search round-trip | P0 |
| Integration | Full RAG pipeline with a real document | P1 |
| API | POST /chat/ with valid query | P0 |
| API | POST /ingest/ with PDF file | P0 |
| API | POST /ingest/ with unsupported file type | P1 |
| API | POST /chat/ before any document ingested | P1 |
| RAG-specific | Retrieval recall on known Q&A pairs | P1 |
| RAG-specific | Empty retrieval case | P1 |
| RAG-specific | Routing accuracy (LLM router) | P2 |
| Security | Oversized file upload | P1 |
| Security | Malformed PDF | P1 |
| Performance | Embedding latency | P2 |

---

## Security Considerations

### Current Issues
1. **No file size limit** on `/ingest/` — a 10GB file would be written to disk and processed
2. **No MIME type validation** — any file extension accepted
3. **No authentication** — any client can ingest documents or query the system
4. **CORS hardcoded** — not a security risk at localhost but fails in deployment
5. **Prompt injection risk** — user queries go directly into LLM calls with no sanitization
6. **Malicious document content** — a PDF could contain injected instructions to the LLM ("Ignore all previous instructions...")
7. **No rate limiting** — unlimited LLM calls from any client
8. **No secrets management** — no API keys in this project (Ollama is local), but the pattern doesn't scale

---

## Performance Considerations

### Bottlenecks
1. **Two LLM calls per query** (router + answer generation) — each is a synchronous Ollama HTTP call
2. **Embedding model loads at startup** — first request is slow until model is warm
3. **FAISS in-memory** — fast for small indexes, but non-scalable
4. **No async LLM calls** — FastAPI is async but LangChain Ollama `.invoke()` is synchronous, blocking the event loop
5. **No response streaming** — UI waits for complete LLM response
6. **No request queuing** — concurrent users will contend on Ollama

---

## Current Strengths

1. **Clean separation of concerns** — loader, embedder, vectorstore, router, API are separate modules
2. **Working RAG pipeline** — the core wiring is correct (embed → store → retrieve → generate)
3. **Proper temp file cleanup** — `finally: os.unlink(tmp_path)` in `ingest.py`
4. **None-guard on vectordb** — prevents crash when no documents are loaded
5. **Hot-reload development setup** — volume mounts in docker-compose for both services
6. **HuggingFace model caching** — `backend-cache` volume prevents re-downloading on restart
7. **Production frontend Dockerfile** — proper multi-stage build with nginx

---

## Current Weaknesses

1. **No text splitting** — documents ingested as whole pages/files, degrading retrieval quality
2. **In-memory FAISS only** — no persistence, every restart requires re-ingestion
3. **Replace-on-upload** — cannot build multi-document knowledge bases
4. **Unpinned dependencies** — non-reproducible builds
5. **No tests** — zero confidence in correctness
6. **No CI/CD** — no automated quality gate
7. **Two LLM calls per query** — unnecessary latency for routing
8. **LLM router is fragile** — unexpected output silently routes to WORKFLOW stub
9. **Hardcoded CORS origin** — not production-ready
10. **`--reload` in production Dockerfile** — development flag in production command
11. **README/code divergence** — Chroma vs FAISS, nonexistent CI/CD listed as feature
12. **No chunking strategy** — the most important RAG tuning lever is missing
13. **No evaluation** — no way to measure retrieval quality

---

## Missing AI Evaluation Capabilities

The most significant gap for a portfolio project claiming "Enterprise AI" is the absence of any evaluation framework. What's missing:

| Capability | Description | Difficulty | Value |
|---|---|---|---|
| Retrieval Precision | Are retrieved chunks relevant to the query? | Medium | Very High |
| Retrieval Recall | Are all relevant chunks retrieved? | Medium | Very High |
| Answer Faithfulness | Does the answer stick to the retrieved context? | High | Very High |
| Answer Relevance | Does the answer address the question? | Medium | High |
| Hallucination detection | Does the answer contain facts not in context? | High | Very High |
| Prompt injection tests | Can user input override system behavior? | Low | High |
| Regression test suite | Do answers stay consistent after model changes? | Medium | High |
| Golden dataset | Known Q&A pairs for deterministic evaluation | Low | Very High |
| CI quality gate | Block deployment on eval score drop | High | Very High |

---

## Recommended Future Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CURRENT STATE                     │
│  Upload → FAISS (in-memory) → Ollama → Answer       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│               TARGET ARCHITECTURE                   │
│                                                     │
│  Document Ingestion Pipeline                        │
│  ├── File validation (type, size, virus scan)       │
│  ├── Text extraction (PDF, DOCX, HTML, etc.)        │
│  ├── Chunking (RecursiveCharacterTextSplitter)      │
│  │   size=512, overlap=64                           │
│  ├── Metadata extraction (source, page, date)       │
│  ├── Embedding (all-mpnet-base-v2 or higher)        │
│  └── Persistent vector store (ChromaDB / Qdrant)   │
│                                                     │
│  Query Pipeline                                     │
│  ├── Input validation / sanitization               │
│  ├── Query embedding                                │
│  ├── Hybrid retrieval (dense + BM25)                │
│  ├── Re-ranking (CrossEncoder)                      │
│  ├── Context construction with citations            │
│  ├── Prompt with system instructions                │
│  └── LLM generation (streaming)                    │
│                                                     │
│  Evaluation Framework (NEW)                         │
│  ├── Golden dataset (Q&A pairs per document)        │
│  ├── Retrieval metrics (precision@k, recall@k)      │
│  ├── Answer faithfulness (LLM-as-judge)             │
│  ├── RAGAS integration                              │
│  └── CI quality gate                               │
│                                                     │
│  Infrastructure (NEW)                               │
│  ├── GitHub Actions CI/CD                          │
│  ├── Persistent ChromaDB volume                    │
│  ├── Auth (JWT / OAuth)                             │
│  ├── Rate limiting                                  │
│  └── Structured logging + monitoring               │
└─────────────────────────────────────────────────────┘
```

---

## Interview Talking Points

1. **"I implemented a full RAG pipeline"** — true, and you can trace it from `loader.py` → `embedder.py` → `vectorstore.py` → `chat.py`
2. **"I used FAISS for vector search"** — be ready to explain why, and acknowledge the trade-off vs. persistent stores
3. **"The system includes intelligent query routing"** — acknowledge the LLM-based router and its fragility, propose rule-based alternative
4. **"all-mpnet-base-v2 produces 768-dim embeddings"** — know the model, its limits (512 token input cap), and why you chose it
5. **"I identified that the system has no chunking"** — this shows architectural awareness
6. **"If I were improving this, I would add chunking, persistence, and an evaluation framework"** — strong answer

---

## Knowledge Gaps to Address Before Interview

### P0 (Must Know)
- How FAISS similarity_search works internally (L2 distance vs. cosine)
- What `all-mpnet-base-v2` produces (768-dim, MPNet, 512 token limit)
- Why chunking matters and how RecursiveCharacterTextSplitter works
- How LangChain `FAISS.from_documents()` actually builds the index
- How `Ollama` class in LangChain connects to the local server

### P1 (Important)
- RAGAS framework for RAG evaluation
- ChromaDB persistent storage as an alternative to in-memory FAISS
- LangChain PromptTemplate vs. f-string (why structured prompts matter)
- What "top-K" means and how to tune it
- Why two LLM calls per query is a design problem

### P2 (Nice to Know)
- MPNet architecture vs. BERT
- HNSW algorithm that FAISS uses internally
- LangChain v0.1 vs. v0.2 migration path (langchain-community split)
