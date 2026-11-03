import os
from pathlib import Path
import faiss
import numpy as np
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool

# Load environment variables from src/.env
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

PDF_PATH = Path(__file__).resolve().parents[2] / "data" / "políticas_da_loja.pdf"


class StorePolicyIndex:
    """Extrai o texto do PDF de políticas da loja e indexa no FAISS com embeddings do Gemini."""

    def __init__(self, pdf_path: Path):
        if not pdf_path.exists():
            raise FileNotFoundError(f"Arquivo de políticas da loja não encontrado: {pdf_path}")

        self.pdf_path = pdf_path
        self.chunks: list[dict] = []
        self._load_and_chunk_pdf()

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )

        texts = [c["content"] for c in self.chunks]
        vectors = np.array(self.embeddings.embed_documents(texts), dtype="float32")
        faiss.normalize_L2(vectors)

        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def _load_and_chunk_pdf(self) -> None:
        reader = PdfReader(str(self.pdf_path))
        for page_num, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                self.chunks.append({"page": page_num, "content": text})

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        query_vec = np.array([self.embeddings.embed_query(query)], dtype="float32")
        faiss.normalize_L2(query_vec)

        scores, indices = self.index.search(query_vec, min(top_k, len(self.chunks)))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:
                results.append(
                    {
                        "page": self.chunks[idx]["page"],
                        "content": self.chunks[idx]["content"],
                        "similarity_score": round(float(score), 4),
                    }
                )
        return results


_policy_index: StorePolicyIndex | None = None


def polict_store() -> StorePolicyIndex:
    """Retorna a instância indexada das políticas da loja (lazy initialization)."""
    global _policy_index
    if _policy_index is None:
        _policy_index = StorePolicyIndex(PDF_PATH)
    return _policy_index


@tool
def query_store_policies(query: str, top_k: int = 3) -> list[dict]:
    """
    Consulta o manual de políticas e procedimentos da loja Empório da Música (PDF).
    Útil para responder dúvidas sobre trocas, devoluções, garantia, frete, prazos de entrega,
    formas de pagamento, parcelamento, horários de funcionamento, endereço, contato e regras de promoções.
    """
    return polict_store().search(query=query, top_k=top_k)
