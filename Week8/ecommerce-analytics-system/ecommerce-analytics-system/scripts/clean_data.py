"""
clean_data.py
-------------
Loads the raw CSVs, cleans them with pandas, validates referential
integrity across tables, and writes cleaned CSVs + a text report
summarizing every issue found and fixed.

Usage:
    python clean_data.py

Input:
    ../data/raw/*.csv
Output:
    ../data/cleaned/*_clean.csv
    ../output/sample_reports/data_quality_report.txt
"""

import os
import re
from datetime import datetime

import pandas as pd

BASE = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE, "..", "data", "raw")
CLEAN_DIR = os.path.join(BASE, "..", "data", "cleaned")
REPORT_DIR = os.path.join(BASE, "..", "output", "sample_reports")
os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

issues_log = []


def log(msg):
    print(msg)
    issues_log.append(msg)


# ---------------------------------------------------------------------------
# clean_customers
# ---------------------------------------------------------------------------
def clean_customers():
    df = pd.read_csv(os.path.join(RAW_DIR, "customers.csv"))

    before = len(df)
    dupes = df.duplicated(subset=["customer_id"], keep="first").sum()
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    log(f"[customers] Removed {dupes} duplicate customer_id rows (kept first). "
        f"{before} -> {len(df)} rows.")

    # normalize name / email whitespace
    df["customer_name"] = df["customer_name"].str.strip()
    df["email"] = df["email"].str.strip().str.lower()

    # standardize registration_date to datetime
    df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    bad_dates = df["registration_date"].isna().sum()
    if bad_dates:
        log(f"[customers] {bad_dates} rows had unparseable registration_date.")

    # unknown customer_type -> REGULAR
    valid_types = {"REGULAR", "PREMIUM", "VIP"}
    bad_types = (~df["customer_type"].isin(valid_types)).sum()
    df.loc[~df["customer_type"].isin(valid_types), "customer_type"] = "REGULAR"
    if bad_types:
        log(f"[customers] {bad_types} rows had invalid customer_type -> set to REGULAR.")

    df.to_csv(os.path.join(CLEAN_DIR, "customers_clean.csv"), index=False)
    return df, validate_emails(df)


def validate_emails(customers_df):
    """Return list of customer_ids with invalid emails (missing @ or domain)."""
    pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    invalid_mask = ~customers_df["email"].astype(str).apply(lambda x: bool(pattern.match(x)))
    invalid_ids = customers_df.loc[invalid_mask, "customer_id"].tolist()
    log(f"[customers] validate_emails(): {len(invalid_ids)} customer_ids have invalid emails "
        f"(sample: {invalid_ids[:5]}).")
    return invalid_ids


# ---------------------------------------------------------------------------
# clean_products
# ---------------------------------------------------------------------------
def clean_products():
    df = pd.read_csv(os.path.join(RAW_DIR, "products.csv"))

    before_names = df["product_name"].copy()
    df["product_name"] = df["product_name"].str.strip().str.title()
    changed = (before_names.str.strip().str.title() != before_names).sum()
    log(f"[products] Normalized product_name (trim + title case) for {changed} rows.")

    df["category"] = df["category"].str.strip().str.title()
    df["subcategory"] = df["subcategory"].str.strip().str.title()

    neg_cost = (df["cost_price"] < 0).sum()
    if neg_cost:
        df = df[df["cost_price"] >= 0]
        log(f"[products] Removed {neg_cost} rows with negative cost_price.")

    dupes = df.duplicated(subset=["product_id"]).sum()
    df = df.drop_duplicates(subset=["product_id"], keep="first")
    if dupes:
        log(f"[products] Removed {dupes} duplicate product_id rows.")

    df.to_csv(os.path.join(CLEAN_DIR, "products_clean.csv"), index=False)
    return df


# ---------------------------------------------------------------------------
# clean_orders
# ---------------------------------------------------------------------------
def parse_mixed_date(value):
    """Try multiple known formats and return a normalized 'YYYY-MM-DD HH:MM:SS' string."""
    if pd.isna(value) or str(value).strip() == "":
        return None
    value = str(value).strip()
    formats = ["%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return None


def clean_orders(valid_customer_ids):
    df = pd.read_csv(os.path.join(RAW_DIR, "orders.csv"), dtype={"customer_id": "object"})

    # Fix date formats (handles DD-MM-YYYY as well as correct format)
    parsed = df["order_date"].apply(parse_mixed_date)
    unparsed = parsed.isna().sum()
    df["order_date"] = parsed
    if unparsed:
        log(f"[orders] {unparsed} order_date values could not be parsed and were set to NULL.")

    # Handle NULL / missing customer_id -> keep as explicit NULL marker, flag count
    missing_cust = df["customer_id"].isna() | (df["customer_id"].astype(str).str.strip() == "")
    n_missing = missing_cust.sum()
    df.loc[missing_cust, "customer_id"] = pd.NA
    log(f"[orders] {n_missing} rows have missing/NULL customer_id (kept as NULL, "
        f"treated as guest/unattributed orders).")

    # Flag customer_ids that don't exist in customers table (orphaned FK)
    known_ids = set(valid_customer_ids)
    df["customer_id_numeric"] = pd.to_numeric(df["customer_id"], errors="coerce")
    orphan_mask = df["customer_id_numeric"].notna() & (~df["customer_id_numeric"].isin(known_ids))
    n_orphan = orphan_mask.sum()
    if n_orphan:
        log(f"[orders] {n_orphan} rows reference a customer_id not present in customers table "
            f"(set to NULL).")
        df.loc[orphan_mask, "customer_id"] = pd.NA
    df = df.drop(columns=["customer_id_numeric"])

    # Standardize status values
    valid_status = {"PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"}
    df["status"] = df["status"].str.upper().str.strip()
    bad_status = (~df["status"].isin(valid_status)).sum()
    if bad_status:
        log(f"[orders] {bad_status} rows had an unrecognized status value.")

    # Flag (but keep, for edge-case testing) future-dated orders
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    future_mask = df["order_date"] > now_str
    n_future = future_mask.sum()
    if n_future:
        log(f"[orders] {n_future} rows have an order_date in the future (kept, flagged for review).")

    dupes = df.duplicated(subset=["order_id"]).sum()
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    if dupes:
        log(f"[orders] Removed {dupes} duplicate order_id rows.")

    df.to_csv(os.path.join(CLEAN_DIR, "orders_clean.csv"), index=False)
    return df


# ---------------------------------------------------------------------------
# clean_order_items + referential integrity
# ---------------------------------------------------------------------------
def check_referential_integrity(order_items_df, valid_order_ids):
    """Find order_items that reference non-existent orders."""
    bad_mask = ~order_items_df["order_id"].isin(valid_order_ids)
    bad_rows = order_items_df.loc[bad_mask]
    log(f"[order_items] check_referential_integrity(): {len(bad_rows)} order_items rows "
        f"reference an order_id that does not exist in orders "
        f"(sample order_ids: {bad_rows['order_id'].unique()[:5].tolist()}).")
    return bad_rows


def clean_order_items(valid_order_ids, valid_product_ids):
    df = pd.read_csv(os.path.join(RAW_DIR, "order_items.csv"))

    bad_rows = check_referential_integrity(df, valid_order_ids)
    df = df[~df.index.isin(bad_rows.index)]
    log(f"[order_items] Dropped {len(bad_rows)} rows with invalid order_id references.")

    bad_product = ~df["product_id"].isin(valid_product_ids)
    n_bad_product = bad_product.sum()
    if n_bad_product:
        df = df[~bad_product]
        log(f"[order_items] Dropped {n_bad_product} rows with invalid product_id references.")

    # discount_percent must be within 0-100; clip out-of-range values and flag them
    invalid_discount = ((df["discount_percent"] < 0) | (df["discount_percent"] > 100)).sum()
    if invalid_discount:
        log(f"[order_items] {invalid_discount} rows had discount_percent outside 0-100; clipped to range.")
        df["discount_percent"] = df["discount_percent"].clip(lower=0, upper=100)

    # negative quantity = returns; keep them but flag as a separate is_return column
    df["is_return"] = df["quantity"] < 0
    n_returns = df["is_return"].sum()
    log(f"[order_items] {n_returns} rows identified as returns (negative quantity), flagged via is_return.")

    zero_qty = (df["quantity"] == 0).sum()
    if zero_qty:
        log(f"[order_items] {zero_qty} rows have quantity = 0 (kept, but contribute 0 revenue).")

    df.to_csv(os.path.join(CLEAN_DIR, "order_items_clean.csv"), index=False)
    return df


def main():
    log(f"Data Quality & Cleaning Report")
    log(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)

    customers_df, invalid_emails = clean_customers()
    products_df = clean_products()
    orders_df = clean_orders(customers_df["customer_id"].tolist())
    order_items_df = clean_order_items(
        orders_df["order_id"].tolist(), products_df["product_id"].tolist()
    )

    log("=" * 70)
    log("Final row counts:")
    log(f"  customers_clean.csv   : {len(customers_df)}")
    log(f"  products_clean.csv    : {len(products_df)}")
    log(f"  orders_clean.csv      : {len(orders_df)}")
    log(f"  order_items_clean.csv : {len(order_items_df)}")

    report_path = os.path.join(REPORT_DIR, "data_quality_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(issues_log))

    print(f"\nCleaned CSVs written to: {os.path.abspath(CLEAN_DIR)}")
    print(f"Report written to: {os.path.abspath(report_path)}")


if __name__ == "__main__":
    main()
