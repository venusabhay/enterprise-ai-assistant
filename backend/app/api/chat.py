from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.task_router import router_prompt
from langchain_community.llms import Ollama
from app.rag.vectorstore import vectordb
import os


router = APIRouter()
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
llm = Ollama(model="llama3.2", base_url=ollama_host)


class ChatRequest(BaseModel):
    query: str


@router.post("/")
def chat(req: ChatRequest):
    try:
        route = llm.invoke(router_prompt.format(query=req.query)).strip()


        if route == "RAG":
            if vectordb.db is None:
                return {"route": "ERROR", "answer": "No documents indexed. Please upload documents first."}
            docs = vectordb.search(req.query)
            context = "\n".join([d.page_content for d in docs])
            answer = llm.invoke(f"Context: {context}\nQuestion: {req.query}")
            return {"route": route, "answer": answer}


        if route == "SUMMARIZE":
            return {"route": route, "answer": llm.invoke(f"Summarize: {req.query}")}


        return {"route": "WORKFLOW", "answer": "Workflow execution coming soon."}
    except Exception as e:
        return {"route": "ERROR", "answer": f"Error processing request: {str(e)}"}