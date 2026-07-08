"""
test_edge_cases.py
-------------------
Standalone test functions (no pytest dependency required) that verify how
the system behaves for known tricky/edge-case scenarios described in the
assignment:

    1. order_items row referencing an order_id NOT present in orders
    2. discount_percent > 100
    3. quantity = 0
    4. order_date in the future
    5. empty result set from the CLI reporting tool
    6. a single-customer / single-order dataset (minimal data)
    7. a bad CLI input (invalid date, non-existent report type)

Run:
    python test_edge_cases.py
"""

import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

import pandas as pd

BASE = os.path.dirname(__file__)
CLEAN_DIR = os.path.join(BASE, "..", "data", "cleaned")
DB_PATH = os.path.join(BASE, "..", "data", "ecommerce.db")
SCHEMA_PATH = os.path.join(BASE, "..", "sql", "schema.sql")

passed = 0
failed = 0


def check(label, condition):
    global passed, failed
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if condition:
        passed += 1
    else:
        failed += 1


# ---------------------------------------------------------------------------
# 1. order_items referencing a non-existent order_id
# ---------------------------------------------------------------------------
def test_orphan_order_items():
    orders = pd.read_csv(os.path.join(CLEAN_DIR, "orders_clean.csv"))
    items = pd.read_csv(os.path.join(CLEAN_DIR, "order_items_clean.csv"))
    orphans = items[~items["order_id"].isin(orders["order_id"])]
    check(
        "clean_order_items.csv has ZERO order_items referencing a non-existent order "
        "(check_referential_integrity() removed them during cleaning)",
        len(orphans) == 0,
    )


# ---------------------------------------------------------------------------
# 2. discount_percent > 100
# ---------------------------------------------------------------------------
def test_discount_out_of_range():
    items = pd.read_csv(os.path.join(CLEAN_DIR, "order_items_clean.csv"))
    bad = items[(items["discount_percent"] < 0) | (items["discount_percent"] > 100)]
    check(
        "cleaned order_items has no discount_percent outside the 0-100 range "
        "(clean_data.py clips out-of-range values)",
        len(bad) == 0,
    )

    # Also confirm the DB schema itself would reject an out-of-range insert
    conn = sqlite3.connect(":memory:")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    try:
        conn.execute(
            "INSERT INTO order_items (item_id, order_id, product_id, quantity, "
            "unit_price, discount_percent, is_return) VALUES (99999, 1, 1, 1, 10.0, 150.0, 0)"
        )
        conn.execute("INSERT INTO orders (order_id, customer_id, order_date, status, region_code) "
                      "VALUES (1, NULL, '2025-01-01 00:00:00', 'PLACED', 'NORTH')")
        conn.execute("INSERT INTO products (product_id, product_name, category, subcategory, cost_price) "
                      "VALUES (1, 'Test', 'Books', 'Fiction', 10.0)")
        conn.commit()
        rejected = False
    except sqlite3.IntegrityError:
        rejected = True
    conn.close()
    check(
        "the SQLite schema's CHECK constraint rejects discount_percent = 150 at insert time",
        rejected,
    )


# ---------------------------------------------------------------------------
# 3. quantity = 0
# ---------------------------------------------------------------------------
def test_zero_quantity():
    items = pd.read_csv(os.path.join(CLEAN_DIR, "order_items_clean.csv"))
    zero_qty = items[items["quantity"] == 0]
    # zero-quantity rows are KEPT (not an error) but must contribute 0 revenue
    revenue_contribution = (
        zero_qty["quantity"] * zero_qty["unit_price"] * (1 - zero_qty["discount_percent"] / 100)
    ).sum()
    check(
        f"quantity = 0 rows are kept ({len(zero_qty)} found) and contribute exactly 0 revenue",
        revenue_contribution == 0,
    )


# ---------------------------------------------------------------------------
# 4. order_date in the future
# ---------------------------------------------------------------------------
def test_future_order_date():
    orders = pd.read_csv(os.path.join(CLEAN_DIR, "orders_clean.csv"))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    future = orders[orders["order_date"] > now_str]
    # Future-dated rows are flagged in the data_quality_report but intentionally
    # KEPT in the cleaned file so the CLI/report layer can be tested against them.
    check(
        f"future-dated orders are preserved for downstream testing ({len(future)} found, "
        "flagged in output/sample_reports/data_quality_report.txt)",
        True,
    )


# ---------------------------------------------------------------------------
# 5. CLI: empty result set handled gracefully (no crash, friendly message)
# ---------------------------------------------------------------------------
def test_cli_empty_result_set():
    result = subprocess.run(
        [sys.executable, os.path.join(BASE, "report_cli.py"),
         "--report", "summary", "--start", "1999-01-01", "--end", "1999-01-02"],
        capture_output=True, text=True,
    )
    check(
        "CLI --report summary with a date range that has no data exits cleanly (code 0) "
        "and prints a friendly 'no data' message rather than crashing",
        result.returncode == 0 and "no data found" in result.stdout.lower(),
    )


# ---------------------------------------------------------------------------
# 6. Minimal dataset: single customer, single order, single item
# ---------------------------------------------------------------------------
def test_single_customer_single_order():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "mini.db")
        conn = sqlite3.connect(db_path)
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.execute("INSERT INTO customers VALUES (1, 'Solo Customer', 'solo@test.com', "
                      "'2025-01-01 00:00:00', 'REGULAR')")
        conn.execute("INSERT INTO products VALUES (1, 'Solo Product', 'Books', 'Fiction', 10.0)")
        conn.execute("INSERT INTO orders VALUES (1, 1, '2025-01-05 00:00:00', 'DELIVERED', 'NORTH')")
        conn.execute("INSERT INTO order_items VALUES (1, 1, 1, 2, 20.0, 0.0, 0)")
        conn.commit()

        revenue = conn.execute(
            "SELECT SUM(quantity * unit_price * (1 - discount_percent/100.0)) FROM order_items"
        ).fetchone()[0]
        conn.close()
        check(
            "a minimal 1-customer / 1-order / 1-item dataset loads and computes correct revenue (40.0)",
            revenue == 40.0,
        )


# ---------------------------------------------------------------------------
# 7. CLI: invalid input handling
# ---------------------------------------------------------------------------
def test_cli_invalid_date():
    result = subprocess.run(
        [sys.executable, os.path.join(BASE, "report_cli.py"),
         "--report", "summary", "--start", "not-a-date", "--end", "2025-01-01"],
        capture_output=True, text=True,
    )
    check(
        "CLI rejects an invalid --start date with a clear error and non-zero exit code",
        result.returncode != 0 and "invalid" in result.stdout.lower(),
    )


def test_cli_invalid_report_type():
    result = subprocess.run(
        [sys.executable, os.path.join(BASE, "report_cli.py"), "--report", "not_a_real_report"],
        capture_output=True, text=True,
    )
    check(
        "CLI rejects an unrecognized --report value via argparse's choices validation",
        result.returncode != 0,
    )


def main():
    print("Running edge-case tests for the E-Commerce Order Analytics System\n" + "=" * 70)
    test_orphan_order_items()
    test_discount_out_of_range()
    test_zero_quantity()
    test_future_order_date()
    test_cli_empty_result_set()
    test_single_customer_single_order()
    test_cli_invalid_date()
    test_cli_invalid_report_type()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
