"""
report_cli.py
-------------
Command-line reporting tool for the E-Commerce Order Analytics System.

Usage examples:
    python report_cli.py --report revenue
    python report_cli.py --report revenue --start 2025-01-01 --end 2025-06-30
    python report_cli.py --report top_customers --limit 5
    python report_cli.py --report retention
    python report_cli.py --report summary --period monthly --start 2025-01-01 --end 2025-01-31
    python report_cli.py --report rfm

Supported --report values:
    revenue         Total revenue per category
    top_customers   Top N customers by total order value
    retention       Cohort retention (month 0-3) per registration cohort
    rfm             RFM segment counts and sample customers
    summary         Period summary report (orders, revenue, unique customers,
                     top 3 products, % change vs previous equal-length period)
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timedelta

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

BASE = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, "..", "data", "ecommerce.db")


def print_table(rows, headers):
    if not rows:
        print("(no data found for the given parameters)")
        return
    if HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        # graceful fallback if tabulate isn't installed
        print(" | ".join(headers))
        print("-" * 60)
        for row in rows:
            print(" | ".join(str(v) for v in row))


def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {os.path.abspath(DB_PATH)}.")
        print("Run scripts/generate_data.py, clean_data.py, and load_db.py first.")
        sys.exit(1)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        return conn
    except sqlite3.Error as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)


def validate_date(date_str, label):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        print(f"ERROR: Invalid {label} date '{date_str}'. Expected format: YYYY-MM-DD.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Report: revenue per category
# ---------------------------------------------------------------------------
def report_revenue(conn, start, end):
    query = """
        SELECT p.category,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS revenue
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN orders o   ON o.order_id   = oi.order_id
        WHERE 1=1
    """
    params = []
    if start:
        query += " AND DATE(o.order_date) >= DATE(?)"
        params.append(start)
    if end:
        query += " AND DATE(o.order_date) <= DATE(?)"
        params.append(end)
    query += " GROUP BY p.category ORDER BY revenue DESC"

    rows = conn.execute(query, params).fetchall()
    print("\nTotal Revenue per Category")
    print_table(rows, ["Category", "Revenue"])


# ---------------------------------------------------------------------------
# Report: top customers
# ---------------------------------------------------------------------------
def report_top_customers(conn, limit, start, end):
    query = """
        SELECT c.customer_id, c.customer_name, c.customer_type,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_value
        FROM customers c
        JOIN orders o       ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id   = o.order_id
        WHERE 1=1
    """
    params = []
    if start:
        query += " AND DATE(o.order_date) >= DATE(?)"
        params.append(start)
    if end:
        query += " AND DATE(o.order_date) <= DATE(?)"
        params.append(end)
    query += " GROUP BY c.customer_id ORDER BY total_value DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    print(f"\nTop {limit} Customers by Total Order Value")
    print_table(rows, ["Customer ID", "Name", "Type", "Total Value"])


# ---------------------------------------------------------------------------
# Report: retention (cohort analysis, month 0-3)
# ---------------------------------------------------------------------------
def report_retention(conn):
    query = """
        WITH cohorts AS (
            SELECT customer_id, strftime('%Y-%m', registration_date) AS cohort_month
            FROM customers
        ),
        cohort_size AS (
            SELECT cohort_month, COUNT(*) AS cohort_customers
            FROM cohorts GROUP BY cohort_month
        ),
        customer_orders AS (
            SELECT DISTINCT o.customer_id, strftime('%Y-%m', o.order_date) AS order_month
            FROM orders o WHERE o.customer_id IS NOT NULL
        ),
        offsets AS (
            SELECT co.customer_id, c.cohort_month,
                (CAST(strftime('%Y', co.order_month || '-01') AS INTEGER) -
                 CAST(strftime('%Y', c.cohort_month || '-01') AS INTEGER)) * 12
                + (CAST(strftime('%m', co.order_month || '-01') AS INTEGER) -
                   CAST(strftime('%m', c.cohort_month || '-01') AS INTEGER)) AS month_offset
            FROM customer_orders co JOIN cohorts c ON c.customer_id = co.customer_id
        ),
        activity AS (
            SELECT cohort_month, month_offset, COUNT(DISTINCT customer_id) AS active_customers
            FROM offsets WHERE month_offset BETWEEN 0 AND 3
            GROUP BY cohort_month, month_offset
        )
        SELECT cs.cohort_month, cs.cohort_customers, a.month_offset, a.active_customers,
               ROUND(100.0 * a.active_customers / cs.cohort_customers, 2) AS retention_percent
        FROM cohort_size cs JOIN activity a ON a.cohort_month = cs.cohort_month
        ORDER BY cs.cohort_month, a.month_offset
    """
    rows = conn.execute(query).fetchall()
    print("\nCohort Retention Analysis (Month 0-3)")
    print_table(rows, ["Cohort Month", "Cohort Size", "Month Offset", "Active", "Retention %"])


# ---------------------------------------------------------------------------
# Report: RFM segments
# ---------------------------------------------------------------------------
def report_rfm(conn):
    query = """
        WITH dataset_max_date AS (SELECT MAX(order_date) AS max_date FROM orders),
        rfm_base AS (
            SELECT o.customer_id,
                   JULIANDAY((SELECT max_date FROM dataset_max_date)) - JULIANDAY(MAX(o.order_date)) AS recency_days,
                   COUNT(DISTINCT o.order_id) AS frequency,
                   SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS monetary
            FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.customer_id IS NOT NULL
            GROUP BY o.customer_id
        ),
        rfm_scored AS (
            SELECT customer_id, recency_days, frequency, monetary,
                   NTILE(4) OVER (ORDER BY recency_days ASC) AS r_score,
                   NTILE(4) OVER (ORDER BY frequency DESC)   AS f_score,
                   NTILE(4) OVER (ORDER BY monetary DESC)    AS m_score
            FROM rfm_base
        ),
        segmented AS (
            SELECT *,
                CASE
                    WHEN r_score = 1 AND f_score = 1 AND m_score = 1 THEN 'Champion'
                    WHEN r_score <= 2 AND f_score <= 2 THEN 'Loyal Customer'
                    WHEN r_score >= 3 AND f_score >= 3 THEN 'At Risk / Churning'
                    ELSE 'Regular'
                END AS rfm_segment
            FROM rfm_scored
        )
        SELECT rfm_segment, COUNT(*) AS num_customers, ROUND(AVG(monetary), 2) AS avg_monetary
        FROM segmented
        GROUP BY rfm_segment
        ORDER BY num_customers DESC
    """
    rows = conn.execute(query).fetchall()
    print("\nRFM Segment Summary")
    print_table(rows, ["Segment", "# Customers", "Avg Monetary Value"])


# ---------------------------------------------------------------------------
# Report: period summary (daily/weekly/monthly)
# ---------------------------------------------------------------------------
def get_period_stats(conn, start, end):
    query = """
        SELECT COUNT(DISTINCT o.order_id) AS num_orders,
               COUNT(DISTINCT o.customer_id) AS unique_customers,
               COALESCE(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 0) AS revenue
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        WHERE DATE(o.order_date) >= DATE(?) AND DATE(o.order_date) <= DATE(?)
    """
    row = conn.execute(query, (start, end)).fetchone()
    return {"num_orders": row[0], "unique_customers": row[1], "revenue": round(row[2] or 0, 2)}


def get_top_products(conn, start, end, limit=3):
    query = """
        SELECT p.product_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS revenue
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN orders o   ON o.order_id   = oi.order_id
        WHERE DATE(o.order_date) >= DATE(?) AND DATE(o.order_date) <= DATE(?)
        GROUP BY p.product_id
        ORDER BY revenue DESC
        LIMIT ?
    """
    return conn.execute(query, (start, end, limit)).fetchall()


def pct_change(new, old):
    if old in (0, None):
        return None
    return round(100.0 * (new - old) / old, 2)


def report_summary(conn, period, start, end):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    if end_dt < start_dt:
        print("ERROR: --end date must not be before --start date.")
        return

    days = (end_dt - start_dt).days + 1
    prev_end_dt = start_dt - timedelta(days=1)
    prev_start_dt = prev_end_dt - timedelta(days=days - 1)

    cur_stats = get_period_stats(conn, start, end)
    prev_stats = get_period_stats(conn, prev_start_dt.strftime("%Y-%m-%d"), prev_end_dt.strftime("%Y-%m-%d"))
    top_products = get_top_products(conn, start, end)

    print(f"\n{period.capitalize()} Summary Report")
    print(f"Period: {start} to {end}  ({days} day(s))")
    print(f"Previous period for comparison: {prev_start_dt.date()} to {prev_end_dt.date()}")

    summary_rows = [
        ["Total Orders", cur_stats["num_orders"], prev_stats["num_orders"],
         pct_change(cur_stats["num_orders"], prev_stats["num_orders"])],
        ["Total Revenue", cur_stats["revenue"], prev_stats["revenue"],
         pct_change(cur_stats["revenue"], prev_stats["revenue"])],
        ["Unique Customers", cur_stats["unique_customers"], prev_stats["unique_customers"],
         pct_change(cur_stats["unique_customers"], prev_stats["unique_customers"])],
    ]
    print_table(summary_rows, ["Metric", "Current Period", "Previous Period", "% Change"])

    print("\nTop 3 Products (by revenue)")
    print_table(top_products, ["Product Name", "Revenue"])


# ---------------------------------------------------------------------------
# Main / argument parsing
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="E-Commerce Order Analytics CLI Reporting Tool"
    )
    parser.add_argument(
        "--report",
        required=True,
        choices=["revenue", "top_customers", "retention", "rfm", "summary"],
        help="Which report to generate.",
    )
    parser.add_argument("--period", choices=["daily", "weekly", "monthly"], default="monthly",
                         help="Reporting period granularity (used for the 'summary' report label).")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD). Required for 'summary'; optional filter for others.")
    parser.add_argument("--end", help="End date (YYYY-MM-DD). Required for 'summary'; optional filter for others.")
    parser.add_argument("--limit", type=int, default=10, help="Number of rows to show (for top_customers). Default 10.")

    args = parser.parse_args()

    if args.start:
        args.start = validate_date(args.start, "--start")
    if args.end:
        args.end = validate_date(args.end, "--end")
    if args.limit is not None and args.limit <= 0:
        print("ERROR: --limit must be a positive integer.")
        sys.exit(1)

    conn = get_connection()

    try:
        if args.report == "revenue":
            report_revenue(conn, args.start, args.end)
        elif args.report == "top_customers":
            report_top_customers(conn, args.limit, args.start, args.end)
        elif args.report == "retention":
            report_retention(conn)
        elif args.report == "rfm":
            report_rfm(conn)
        elif args.report == "summary":
            if not args.start or not args.end:
                print("ERROR: --report summary requires both --start and --end dates.")
                sys.exit(1)
            report_summary(conn, args.period, args.start, args.end)
    except sqlite3.Error as e:
        print(f"DATABASE ERROR: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
