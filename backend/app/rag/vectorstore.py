from langchain_community.vectorstores import FAISS
from .embedder import embedder


class VectorDB:
    def __init__(self):
        self.db = None

    def build(self, docs):
        self.db = FAISS.from_documents(docs, embedder)

    def search(self, query):
        return self.db.similarity_search(query, k=5)


vectordb = VectorDB()