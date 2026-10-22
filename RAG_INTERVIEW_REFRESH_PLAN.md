# RAG Interview Refresh Plan
> Hands-on recovery plan based on THIS project's actual code  
> Designed for a Senior SDET/Architect re-engaging with an existing project  
> Estimated total time: 7 days (2-3 hours/day)

---

## Concept Priority Map

### P0 — Must Know Before Any Interview

| Concept | Why It Matters Here | Where to Find It |
|---|---|---|
| FAISS similarity_search | Core of retrieval — you call it directly | `vectorstore.py:13` |
| HuggingFace sentence-transformers | Your embedding model — know its limits | `embedder.py:3` |
| LangChain `FAISS.from_documents()` | How your index is built | `vectorstore.py:10` |
| PyPDFLoader behavior | One Document per page — critical gap | `loader.py:8` |
| RAG pipeline (end-to-end) | Can you draw it on a whiteboard? | `chat.py:24-29` |
| In-memory vs. persistent FAISS | Why your index dies on restart | `vectorstore.py:9` |
| Module-level singleton in Python | Why `vectordb` is shared across requests | `vectorstore.py:16` |
| LangChain PromptTemplate | What it does, why over f-strings | `task_router.py:4` |
| OLLAMA_HOST and host.docker.internal | How containerized app reaches host LLM | `docker-compose.yml:11` |
| Cosine similarity | How FAISS ranks results | FAISS docs / embedder.py |

### P1 — Important

| Concept | Why It Matters Here | Where to Find It |
|---|---|---|
| RecursiveCharacterTextSplitter | The biggest missing piece — chunking | Not in project (add it) |
| FAISS `add_documents()` | How to fix the "replace on upload" bug | LangChain FAISS docs |
| FAISS `save_local()` / `load_local()` | How to add persistence | LangChain FAISS docs |
| RAGAS evaluation metrics | What a senior interviewer will ask about | RAGAS docs |
| ChromaDB as alternative | Persistent vector store option | Not in project |
| FastAPI CORS middleware | Why it's hardcoded, what breaks in prod | `main.py:11-17` |
| Uvicorn `--reload` flag | Why it's wrong in the production Dockerfile | `backend/Dockerfile:21` |
| LangChain-community package split | Why imports use `langchain_community` | All backend imports |
| all-mpnet-base-v2 token limit | 512 tokens — silent truncation on long docs | `embedder.py:3` |
| Two-LLM-call pattern | Why it's expensive and fragile | `chat.py:21,29` |

### P2 — Nice to Know

| Concept | Why It Matters Here |
|---|---|
| MPNet architecture vs. BERT | Background on your embedding model |
| HNSW algorithm in FAISS | What happens inside similarity_search |
| LangChain LCEL pipeline | Modern LangChain pattern (not used here, but may be asked) |
| BM25 hybrid retrieval | How to improve beyond pure dense retrieval |
| Cross-encoder re-ranking | Second-stage retrieval quality improvement |
| LangSmith / Langfuse | LLM observability tooling |
| RAGAS faithfulness scoring | Deep dive into the metric |
| vLLM / TGI | Production LLM serving alternatives to Ollama |

---

## 7-Day Hands-On Refresh Plan

---

### DAY 1 — Re-read the Codebase (2 hours)
**Goal:** Rebuild a complete mental model of the system.

**Tasks:**
1. Read `backend/app/main.py` → trace all router registrations
2. Read `backend/app/api/ingest.py` + `loader.py` → understand the ingestion flow
3. Read `backend/app/rag/vectorstore.py` + `embedder.py` → understand the vector store
4. Read `backend/app/api/chat.py` → trace the two-LLM-call pattern
5. Read `backend/app/agents/task_router.py` → understand the routing prompt
6. Read `docker-compose.yml` → understand the container layout

**Key exercise:**
- Without looking at the code, draw the full architecture on paper:
  ```
  User → UI → POST /chat/ → router → FAISS search → LLM → answer
  User → UI → POST /ingest/ → loader → embedder → FAISS
  ```
- Can you name the file responsible for each box? If not, re-read.

**Verbal practice:**
> Say out loud: "When a user uploads a document, it goes to [function] in [file], which calls [class] in [file], which builds a [what?] by calling [what?]..."

---

### DAY 2 — Embeddings Deep Dive (2-3 hours)
**Goal:** Understand all-mpnet-base-v2 deeply enough to defend every design choice.

**Tasks:**
1. Open `embedder.py` — read the one line of code
2. Run this locally (if Python/pip available):
   ```python
   from langchain_community.embeddings import HuggingFaceEmbeddings
   embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
   v1 = embedder.embed_query("quarterly revenue increased")
   v2 = embedder.embed_query("annual profits grew")
   v3 = embedder.embed_query("the cat sat on the mat")
   # Compare: v1 vs v2 should be similar, v1 vs v3 should be different
   ```
3. Intentionally break it: pass a 600-word string to `embed_query()` — observe silent truncation
4. Check vector dimensions: `len(v1)` should be 768

**Key questions to answer verbally:**
- Why 768 dimensions?
- What does the model do to text longer than 512 tokens?
- Why use the same model for documents AND queries?
- What's the difference between a bi-encoder and a cross-encoder?
- What would you do if your documents are in a specialized domain (medical, legal, financial)?

**Experiment:**
- Try `all-MiniLM-L6-v2` (384-dim, faster) — how would you swap it in the project?
- What breaks if you embed documents with model A and query with model B?

---

### DAY 3 — FAISS and Retrieval (2-3 hours)
**Goal:** Understand what FAISS is doing and what top-K means in practice.

**Tasks:**
1. Open `vectorstore.py` — read all 16 lines
2. Run locally:
   ```python
   from langchain_community.vectorstores import FAISS
   from langchain_community.embeddings import HuggingFaceEmbeddings
   from langchain_core.documents import Document

   embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
   docs = [
       Document(page_content="FAISS is a library for efficient similarity search"),
       Document(page_content="Python is a programming language"),
       Document(page_content="Vector databases store embedding vectors"),
   ]
   db = FAISS.from_documents(docs, embedder)
   results = db.similarity_search("find similar vectors", k=2)
   for r in results:
       print(r.page_content)
   ```
3. Add persistence: after `from_documents`, call `db.save_local("./test_index")` — check what files are created
4. Reload: `db2 = FAISS.load_local("./test_index", embedder, allow_dangerous_deserialization=True)`
5. Add a document incrementally: `db.add_documents([Document(page_content="New document")])`

**Intentionally break it:**
- Try `similarity_search_with_score()` — what do the scores look like? (Lower is more similar for L2)
- Call `db.search()` with a query completely unrelated to any document — what does FAISS return? (It always returns k results — there's no "no match" response)

**Key questions to answer verbally:**
- What is the difference between `from_documents()` and `add_documents()`?
- What happens if you call `from_documents()` twice? (Creates new index — old one gone)
- What is the difference between L2 distance and cosine similarity?
- Why does FAISS always return k results even if nothing is relevant?
- What is a similarity threshold and how would you implement one?

---

### DAY 4 — Chunking (the Missing Piece) (2-3 hours)
**Goal:** Understand why chunking matters and how to add it to this project.

**Tasks:**
1. Identify the gap: `loader.py` has no `TextSplitter` — documents go in whole
2. Read about `RecursiveCharacterTextSplitter` from LangChain
3. Implement it locally as an experiment (do NOT modify the project files):
   ```python
   from langchain.text_splitter import RecursiveCharacterTextSplitter

   splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
   docs = splitter.split_documents(raw_docs)  # from PyPDFLoader
   ```
4. Compare: take a 3-page PDF, ingest with and without chunking
5. Run the same query against both indexes and compare the retrieved content

**Experiment — break it intentionally:**
- Set `chunk_size=50` — observe over-fragmentation (tiny, meaningless chunks)
- Set `chunk_size=2000, chunk_overlap=0` — observe under-chunking (whole pages again)
- Set `chunk_overlap=500` (more than half chunk_size) — observe excessive duplication

**Key questions to answer verbally:**
- What is chunk size and chunk overlap?
- Why does chunk_overlap exist?
- What is the tradeoff between chunk_size=256 and chunk_size=1024?
- What separator strategy does `RecursiveCharacterTextSplitter` use?
- How does chunking affect the number of vectors in the index?
- How does chunking affect the context quality sent to the LLM?

---

### DAY 5 — LLM Router and Prompt Engineering (2 hours)
**Goal:** Understand the routing logic, its fragility, and how to improve it.

**Tasks:**
1. Open `task_router.py` and `chat.py` together
2. Trace: what happens when the LLM returns "rag" (lowercase)?
   - `route = llm.invoke(...).strip()` → "rag"
   - `if route == "RAG"` → False
   - Falls through to WORKFLOW stub
3. Identify all failure modes (see interview.md Q18)
4. Design a fix: add `.upper()` after `.strip()`, add few-shot examples to the prompt
5. Design an alternative: rule-based router using keyword matching

**Experiment:**
- Craft a query that should be RAG but might confuse the router: "Tell me about the document I uploaded"
- Craft a query that might trick it: "Summarize the main points and also answer the question about Q3 revenue"

**Key questions to answer verbally:**
- Why is using an LLM for routing expensive?
- What are the failure modes of the current routing prompt?
- How would you make the router deterministic?
- What is a PromptTemplate and why is it better than an f-string for this use case?
- What would few-shot examples look like for this routing prompt?

---

### DAY 6 — Docker Deep Dive (2 hours)
**Goal:** Understand the full Docker setup and be able to explain every line in docker-compose.yml.

**Tasks:**
1. Read `docker-compose.yml` line by line — for every key, answer: "why is this here?"
2. Read `backend/Dockerfile` — identify the anti-pattern (`--reload` in CMD)
3. Read `ui/Dockerfile` and `ui/Dockerfile.prod` — compare them
4. Read `ui/nginx.conf` — understand the SPA routing and API proxy
5. Trace the `host.docker.internal` path: browser → frontend container → backend container → host Ollama

**Key questions to answer verbally:**
- What does `volumes: - ./backend:/app` do and why is it only safe for development?
- What does `- /app/__pycache__` do? (Anonymous volume to prevent host's pycache from masking container's)
- What does `extra_hosts: - "host.docker.internal:host-gateway"` do?
- What does `depends_on: backend` guarantee vs. what it doesn't?
- What is the difference between `backend-cache:/root/.cache` (named volume) and `./backend:/app` (bind mount)?
- Why does the production nginx config have `try_files $uri $uri/ /index.html`?
- What is the multi-stage build in `Dockerfile.prod` and why does it produce a smaller image?

**Break it intentionally:**
- Remove `extra_hosts` from docker-compose.yml — what error would you see?
- Remove the `backend-cache` volume — what happens on first startup? (Model re-download)
- Change `OLLAMA_HOST` to `http://localhost:11434` — why would it break inside Docker?

---

### DAY 7 — Testing Strategy + Interview Practice (3 hours)
**Goal:** Articulate a complete test strategy and answer scenario questions confidently.

**Tasks:**
1. Write (don't run, just write) three test functions for this project:
   ```python
   # test_loader.py
   def test_pdf_uses_pypdf_loader():
       # assert DocumentLoader.load("test.pdf") calls PyPDFLoader
       pass

   # test_vectorstore.py
   def test_build_creates_db():
       # assert vectordb.db is not None after build()
       pass

   def test_search_returns_k_results():
       # assert len(vectordb.search("query")) == 5
       pass
   ```
2. Design (in writing) the golden dataset: pick 3 questions from any domain document you have, write expected answers
3. Practice answering scenario questions from Level 10 in `interview.md` (Q44-Q48) out loud
4. Practice the 2-minute project explanation 3 times — time yourself

**Key questions to confirm you can answer without notes:**
- Walk me through a complete RAG query (name every function and file)
- What are the three biggest weaknesses of this project?
- How would you add chunking to this project?
- How would you add persistence to FAISS?
- How would you test that retrieval works correctly?
- What is all-mpnet-base-v2 and why did you use it?
- Why FAISS instead of ChromaDB?

---

## Hands-On Exercises Reference

| Exercise | Purpose | Files Involved |
|---|---|---|
| Draw architecture from memory | Test mental model | All |
| Embed two similar sentences, compare similarity scores | Understand embeddings | `embedder.py` |
| Add a second document without replacing the first | Fix the replace-on-upload bug | `vectorstore.py` |
| Add `save_local()` after `build()` | Add persistence | `vectorstore.py` |
| Add `RecursiveCharacterTextSplitter` to `loader.py` | Add chunking | `loader.py` |
| Add `.upper()` to router comparison | Fix case sensitivity bug | `chat.py` |
| Add file size limit to `/ingest/` | Add security control | `ingest.py` |
| Remove `--reload` from production Dockerfile | Fix anti-pattern | `backend/Dockerfile` |
| Write a pytest unit test for `DocumentLoader` | Test familiarity | `loader.py` |
| Add metadata (filename, page) to ingest | Improve source attribution | `loader.py`, `ingest.py` |

---

## Suggested Commands to Run

```bash
# Start the app (requires Ollama running locally with llama3.2 pulled)
cd /Users/abhay/git-venusabhay/enterprise-ai-assistant
docker-compose up --build

# Check health
curl http://localhost:8000/health/

# Test ingest with a real PDF
curl -X POST http://localhost:8000/ingest/ \
  -F "file=@/path/to/your/document.pdf"

# Test chat (requires a document to be ingested first)
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'

# Check API docs
open http://localhost:8000/docs

# Stop and remove volumes (resets FAISS state)
docker-compose down -v
```

---

## Interview Practice Sequence

### Recommended practice order (work through these in this sequence):

**Session 1** (Day 1): Architecture overview — "Walk me through the project"
**Session 2** (Day 2): RAG fundamentals — "What is RAG and how did you implement it?"
**Session 3** (Day 3): Embeddings and FAISS — "How does retrieval work?"
**Session 4** (Day 4): Chunking and the missing piece — "What would you improve?"
**Session 5** (Day 5): LLM router — "Why two LLM calls? What are the failure modes?"
**Session 6** (Day 6): Docker — "Explain the infrastructure"
**Session 7** (Day 7): Testing + scenario questions — "How would you test this?"

For each session, practice:
1. First answer without notes
2. Check your answer against ARCHITECTURE_REVIEW.md or interview.md
3. Fill gaps
4. Answer again without notes

---

## Common Interview Traps and How to Handle Them

**Trap: "You said Chroma Vector Store in your README but the code uses FAISS."**
Answer: "You're right, I identified that discrepancy in my analysis. The README was written at a planning stage — the implementation ended up using FAISS because it's simpler to set up in-process without a separate service. In a production system, I'd migrate to ChromaDB or Qdrant for persistence. The README should have been updated."

**Trap: "Your CI/CD is listed as a feature but there are no GitHub Actions workflows."**
Answer: "Correct — that was aspirational in the README. I identified this as the most critical infrastructure gap. Here's exactly what I would implement: [describe the GitHub Actions pipeline from Q35 in interview.md]."

**Trap: "How much does this cost to run at scale?"**
Answer: "At dev/demo scale with local Ollama — zero cost. At production scale the main cost drivers would be: LLM inference tokens (if switching to a cloud provider like Anthropic/OpenAI), vector store hosting, and compute for the embedding model. I'd reduce costs by: caching embeddings, caching LLM responses for repeated queries, eliminating the router LLM call, and optimizing chunk size to minimize context length."

**Trap: "What's the difference between your implementation and just using LangChain's `RetrievalQA` chain?"**
Answer: "The manual implementation in this project does exactly what `RetrievalQA` would do, but written out explicitly — which actually has an educational advantage for interviews because I can explain each step. `RetrievalQA` would handle the retriever + LLM chain in one call, add better prompt templates, and support source documents in the response. The current manual implementation has no prompt structure for the answer generation step (just a raw f-string), which I'd improve with a proper PromptTemplate."
