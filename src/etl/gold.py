from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def merge_orders_with_customers(orders: pd.DataFrame, customers: pd.DataFrame) -> None:
    """
    Merge orders DataFrame with customers DataFrame on 'customer_id'.

    Parameters:
    orders (pd.DataFrame): DataFrame containing order data.
    customers (pd.DataFrame): DataFrame containing customer data.

    Returns:
    CSV File: Merged DataFrame in CSV format with order and customer information.
    """
    merged_df = orders.merge(
        customers[["customer_id", "name", "email"]],
        on="customer_id",
        how="left"
    )
    merged_df.to_csv(DATA_DIR / "merged_orders_customers.csv", index=False)


def merge_products_with_promotions(products: pd.DataFrame, promotions: pd.DataFrame) -> None:
    """
    Merge products DataFrame with promotions DataFrame on 'product_id'.

    Parameters:
    products (pd.DataFrame): DataFrame containing product data.
    promotions (pd.DataFrame): DataFrame containing promotion data.

    Returns:
    CSV File: Merged DataFrame in CSV format with product and promotion information.
    """
    df_products_with_promotion = products.merge(
        promotions[["product_id", "discount_percent", "description", "is_active"]],
        on="product_id",
        how="left"
    )
    df_products_with_promotion.to_csv(DATA_DIR / "merged_products_promotions.csv", index=False)


if __name__ == "__main__":
    # Example usage
    orders_df = pd.read_csv(DATA_DIR / "desafio_tecnico_ai_eng - orders.csv")
    customers_df = pd.read_csv(DATA_DIR / "desafio_tecnico_ai_eng - customers.csv")
    merge_orders_with_customers(orders_df, customers_df)

    products_df = pd.read_csv(DATA_DIR / "desafio_tecnico_ai_eng - products.csv")
    promotions_df = pd.read_csv(DATA_DIR / "desafio_tecnico_ai_eng - promotions.csv")
    merge_products_with_promotions(products_df, promotions_df)