# Enterprise AI Assistant

A full-stack AI assistant with RAG (Retrieval-Augmented Generation) capabilities, document ingestion, and intelligent query routing.

## Features

- 🤖 RAG pipeline with vector search
- 📄 Document ingestion (PDF, TXT, DOC, DOCX)
- 🎯 Intelligent query routing (RAG/Summarize/Workflow)
- 💬 Real-time chat interface
- 🐳 Fully Dockerized
- 🔄 Hot-reload for development

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.ai) (for local LLM)
  ```powershell
  # Install and pull the model
  ollama pull llama3.2
  ```

## Quick Start

### Using Docker (Recommended)

1. **Start Ollama** on your host machine

2. **Run the application:**
   ```powershell
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Stop the application:**
   ```powershell
   docker-compose down
   ```

For detailed Docker instructions, see [README.Docker.md](README.Docker.md)

### Local Development (Without Docker)

#### Backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```powershell
cd ui
npm install
npm run dev
```

## API Endpoints

- `POST /chat/` - Send chat queries
- `POST /ingest/` - Upload documents for indexing
- `GET /health/` - Health check

## Usage

1. **Upload Documents**: Click the "📄 Upload Document" button in the UI
2. **Ask Questions**: Type your question in the chat and press Enter
3. **Get Answers**: The AI will search your documents and provide relevant answers

## Project Structure

```
enterprise-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── api/              # API endpoints
│   │   ├── rag/              # RAG pipeline
│   │   └── agents/           # Query routing
│   ├── Dockerfile
│   └── requirements.txt
├── ui/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api.js           # API client
│   │   └── App.jsx          # Main app
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml

```

## Tech Stack

**Backend:**
- FastAPI
- LangChain
- HuggingFace Embeddings
- Chroma Vector Store
- Ollama (llama3.2)

**Frontend:**
- React
- Vite
- Tailwind CSS

**Infrastructure:**
- Docker & Docker Compose
- Nginx (production)
