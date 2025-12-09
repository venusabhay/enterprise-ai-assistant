from langchain_community.embeddings import HuggingFaceEmbeddings

embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")