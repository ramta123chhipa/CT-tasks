"""
load_db.py
----------
Creates the SQLite database using sql/schema.sql and loads the cleaned
CSV files into it. Then verifies row counts and relationships.

Usage:
    python load_db.py
Output:
    ../data/ecommerce.db
"""

import os
import sqlite3

import pandas as pd

BASE = os.path.dirname(__file__)
CLEAN_DIR = os.path.join(BASE, "..", "data", "cleaned")
SQL_DIR = os.path.join(BASE, "..", "sql")
DB_PATH = os.path.join(BASE, "..", "data", "ecommerce.db")


def build_schema(conn):
    with open(os.path.join(SQL_DIR, "schema.sql"), "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)


def load_table(conn, csv_name, table_name, columns):
    df = pd.read_csv(os.path.join(CLEAN_DIR, csv_name))
    df = df[columns]
    df.to_sql(table_name, conn, if_exists="append", index=False)
    return len(df)


def verify(conn):
    cur = conn.cursor()
    print("\nRow counts:")
    for table in ["customers", "products", "orders", "order_items"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table:<15}: {cur.fetchone()[0]}")

    print("\nReferential integrity checks:")
    cur.execute("""
        SELECT COUNT(*) FROM orders
        WHERE customer_id IS NOT NULL
          AND customer_id NOT IN (SELECT customer_id FROM customers)
    """)
    print(f"  orphaned orders.customer_id       : {cur.fetchone()[0]}")

    cur.execute("""
        SELECT COUNT(*) FROM order_items
        WHERE order_id NOT IN (SELECT order_id FROM orders)
    """)
    print(f"  orphaned order_items.order_id     : {cur.fetchone()[0]}")

    cur.execute("""
        SELECT COUNT(*) FROM order_items
        WHERE product_id NOT IN (SELECT product_id FROM products)
    """)
    print(f"  orphaned order_items.product_id   : {cur.fetchone()[0]}")


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    print("Building schema ...")
    build_schema(conn)

    print("Loading customers ...")
    n = load_table(conn, "customers_clean.csv", "customers",
                    ["customer_id", "customer_name", "email", "registration_date", "customer_type"])
    print(f"  -> {n} rows")

    print("Loading products ...")
    n = load_table(conn, "products_clean.csv", "products",
                    ["product_id", "product_name", "category", "subcategory", "cost_price"])
    print(f"  -> {n} rows")

    print("Loading orders ...")
    n = load_table(conn, "orders_clean.csv", "orders",
                    ["order_id", "customer_id", "order_date", "status", "region_code"])
    print(f"  -> {n} rows")

    print("Loading order_items ...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, "order_items_clean.csv"))
    df["is_return"] = df["is_return"].astype(int)
    df = df[["item_id", "order_id", "product_id", "quantity", "unit_price",
             "discount_percent", "is_return"]]
    df.to_sql("order_items", conn, if_exists="append", index=False)
    print(f"  -> {len(df)} rows")

    conn.commit()
    verify(conn)
    conn.close()

    print(f"\nDatabase written to: {os.path.abspath(DB_PATH)}")


if __name__ == "__main__":
    main()
