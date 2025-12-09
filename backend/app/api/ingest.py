from fastapi import APIRouter, UploadFile
from app.rag.loader import DocumentLoader
from app.rag.vectorstore import vectordb
import tempfile
import os


router = APIRouter()


@router.post("/")
def ingest(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        try:
            docs = DocumentLoader.load(tmp_path)
            vectordb.build(docs)
            return {"status": "indexed", "chunks": len(docs)}
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        return {"status": "error", "message": f"Failed to process document: {str(e)}"}