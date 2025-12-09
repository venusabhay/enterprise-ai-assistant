from langchain_community.document_loaders import PyPDFLoader, TextLoader


class DocumentLoader:
    @staticmethod
    def load(path: str):
        if path.endswith(".pdf"):
            return PyPDFLoader(path).load()
        return TextLoader(path).load()