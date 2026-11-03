from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.tools import tool

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class TfidfCSVSearcher:
    """Indexa um arquivo CSV com TF-IDF e permite buscar as linhas mais relevantes."""

    def __init__(self, csv_path: Path, text_columns: list[str]):
        self.df = pd.read_csv(csv_path)
        self.text_columns = text_columns

        # Concatena as colunas escolhidas em um único texto por linha para vetorização
        self.corpus = (
            self.df[self.text_columns]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.lower()
        )

        # Cria a matriz TF-IDF (ngram_range=(1, 2) ajuda a capturar nomes compostos e termos exatos)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Retorna os top_k registros mais similares à query usando similaridade de cosseno."""
        query_vec = self.vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Ordena os índices do maior score para o menor
        top_indices = similarities.argsort()[::-1][:top_k]

        results = []
        clean_df = self.df.astype(object).where(self.df.notna(), None)
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0:
                row_dict = clean_df.iloc[idx].to_dict()
                row_dict["similarity_score"] = round(score, 4)
                results.append(row_dict)

        return results


# Inicializa os buscadores para cada tabela Gold
orders_searcher = TfidfCSVSearcher(
    csv_path=DATA_DIR / "merged_orders_customers.csv",
    text_columns=[
        "order_id",
        "customer_id",
        "name",
        "email",
        "status",
        "payment_method",
        "tracking_code",
        "order_date",
        "estimated_delivery",
        "notes",
    ],
)

products_searcher = TfidfCSVSearcher(
    csv_path=DATA_DIR / "merged_products_promotions.csv",
    text_columns=[
        "product_id",
        "name",
        "description_x",
        "specs",
        "status",
        "description_y",
    ],
)


@tool
def query_orders_customers(query: str, top_k: int = 5) -> list[dict]:
    """
    Busca pedidos e clientes usando TF-IDF.
    Útil para consultar status de entrega, código de rastreio, dados de clientes ou histórico de pedidos.
    """
    return orders_searcher.search(query=query, top_k=top_k)


@tool
def query_products_promotions(query: str, top_k: int = 5) -> list[dict]:
    """
    Busca produtos, estoque e promoções usando TF-IDF.
    Útil para verificar preços, especificações técnicas, quantidade em estoque e descontos ativos.
    """
    return products_searcher.search(query=query, top_k=top_k)


if __name__ == "__main__":
    print("=== Teste 1: Busca em Pedidos e Clientes ===")
    res_orders = query_orders_customers.invoke({"query": "Pedro Henrique Oliveira", "top_k": 2})
    for r in res_orders:
        print(r)

    print("\n=== Teste 2: Busca em Produtos e Promoções ===")
    res_products = query_products_promotions.invoke({"query": "violão nylon iniciante yamaha", "top_k": 2})
    for r in res_products:
        print(r)
