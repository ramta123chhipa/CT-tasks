# E-Commerce Order Analytics System

**Intern Mini Project — Celebal Technologies**
Skills tested: Python, SQL, Problem Solving

An end-to-end analytics pipeline that generates realistic (and intentionally
messy) e-commerce data, cleans it with pandas, loads it into a SQL database
with proper constraints, runs a full suite of SQL analytics (joins,
aggregations, window functions, CTEs, cohort/retention, RFM segmentation),
and serves the results through a command-line reporting tool.

---

## 1. System Architecture

```
                ┌─────────────────────┐
                │  generate_data.py   │   Faker + random
                │  (Step 1)           │   -> data/raw/*.csv (messy, on purpose)
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   clean_data.py     │   pandas
                │  (Step 2)           │   -> data/cleaned/*_clean.csv
                └──────────┬───────────┘   -> output/sample_reports/data_quality_report.txt
                           │
                           ▼
                ┌─────────────────────┐
                │    load_db.py       │   sqlite3 + sql/schema.sql
                │  (Step 3)           │   -> data/ecommerce.db (PK/FK/CHECK constraints)
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  sql/*.sql          │   Joins, window functions, CTEs,
                │  (Steps 4-7)        │   cohort analysis, RFM segmentation
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   report_cli.py     │   argparse + sqlite3 + tabulate
                │  (Step 8)           │   -> formatted terminal reports
                └─────────────────────┘

                ┌─────────────────────┐
                │ test_edge_cases.py  │   Runs independently against the
                │  (Step 9)           │   cleaned data / DB / CLI to verify
                └─────────────────────┘   edge-case behaviour
```

Each stage reads only from the previous stage's output, so any stage can be
re-run independently (e.g. re-running `clean_data.py` after fixing a bug
doesn't require regenerating raw data).

### Data model

| Table         | Grain                | Key relationships                              |
|---------------|-----------------------|-------------------------------------------------|
| `customers`   | 1 row / customer       | —                                               |
| `products`    | 1 row / product        | —                                               |
| `orders`      | 1 row / order          | `customer_id` → `customers.customer_id` (nullable — guest orders) |
| `order_items` | 1 row / line item      | `order_id` → `orders.order_id`, `product_id` → `products.product_id` |

`revenue` is computed consistently everywhere as:

```
revenue = quantity * unit_price * (1 - discount_percent / 100)
```

Negative `quantity` values represent returns, so returns automatically net
out of revenue totals without any special-casing.

---

## 2. Intentional Data Quality Issues (and how they're handled)

| Issue                                                | Injected in `generate_data.py` | Handled in `clean_data.py`                                |
|-------------------------------------------------------|:---:|-------------------------------------------------------------|
| Missing/NULL `customer_id` on orders (~5%)             | | Kept as `NULL`, treated as guest/unattributed orders          |
| Negative `quantity` on order_items (~3%, returns)       | | Kept, flagged with an `is_return` column                     |
| `order_date` in wrong format (`DD-MM-YYYY`)             | | Parsed with multiple format attempts, normalized to `YYYY-MM-DD HH:MM:SS` |
| Messy `product_name` (extra spaces / mixed case)        | | Trimmed + title-cased                                        |
| Invalid emails (missing `@` or domain) (~2%)            | | Detected via regex in `validate_emails()`, reported (not silently dropped) |
| `order_items` referencing a non-existent `order_id`     | | Detected via `check_referential_integrity()` and dropped      |
| `order_items` referencing a non-existent `product_id`   | | Dropped, logged                                               |
| `discount_percent` outside 0–100                        | | Clipped to valid range, logged                                |
| Duplicate `customer_id` / `order_id` rows                | | De-duplicated, kept first occurrence                          |
| `quantity = 0`                                          | | Kept (valid edge case — contributes 0 revenue)                |
| Future-dated orders                                      | | Kept and flagged for review (useful for CLI edge-case testing) |

Every issue found is written to
`output/sample_reports/data_quality_report.txt` with row counts, so the
cleaning step is fully auditable.

---

## 3. How to Run

### Prerequisites

```bash
pip install faker pandas tabulate
```

(`sqlite3` ships with Python's standard library — no separate install needed.)

### Step-by-step

```bash
cd scripts

# 1. Generate messy raw data -> ../data/raw/*.csv
python generate_data.py

# 2. Clean it with pandas -> ../data/cleaned/*_clean.csv
#    + ../output/sample_reports/data_quality_report.txt
python clean_data.py

# 3. Build schema + load cleaned data -> ../data/ecommerce.db
python load_db.py

# 4. Run the CLI reporting tool
python report_cli.py --report revenue
python report_cli.py --report top_customers --limit 10
python report_cli.py --report retention
python report_cli.py --report rfm
python report_cli.py --report summary --period monthly --start 2025-06-01 --end 2025-06-30

# 5. (Optional) Run the edge-case test suite
python test_edge_cases.py
```

### CLI Reference

```
python report_cli.py --report <TYPE> [options]

--report {revenue,top_customers,retention,rfm,summary}   (required)
--period {daily,weekly,monthly}                          (label only, default: monthly)
--start YYYY-MM-DD                                        (optional filter; required for 'summary')
--end   YYYY-MM-DD                                        (optional filter; required for 'summary')
--limit N                                                  (top_customers row count, default: 10)
```

The `summary` report shows total orders, revenue, unique customers, the top
3 products, and a percentage change against the immediately preceding
period of equal length.

---

## 4. SQL Analytics Included

**`sql/schema.sql`** — table definitions with `PRIMARY KEY`, `FOREIGN KEY`,
`NOT NULL`, and `CHECK` constraints (e.g. `discount_percent BETWEEN 0 AND 100`),
plus supporting indexes.

**`sql/aggregations.sql`** (Step 4 — Joins & Aggregations)
- Total revenue per category / per customer per month
- Top 10 customers by total order value
- Month-wise order count (last 12 months)
- Top products by quantity sold and revenue
- Average Order Value (AOV) by customer segment
- Customers who never had a delivered order
- Products with more returns than purchases
- Return rate per category

**`sql/window_functions.sql`** (Step 5 — Window Functions & CTEs)
- Running total of revenue per region (`SUM() OVER`)
- `DENSE_RANK()` of products by revenue within category
- `LAG()`/`LEAD()` gap-between-orders analysis with an "At Risk" flag
- Multi-level CTE: monthly revenue → High/Medium/Low categorization → counts
- `NTILE(4)` customer quartiles (Platinum/Gold/Silver/Bronze)
- Year-over-year revenue comparison
- `FIRST_VALUE`/`LAST_VALUE` category-shift detection
- Cumulative revenue distribution (Pareto-style analysis)
- Self-join "frequently bought together" product pairs

**`sql/cohort_analysis.sql`** (Steps 6 & 7 — Cohort/Retention & Segmentation)
- Cohort-by-registration-month retention (month 0–3)
- Churned vs. repeat customer classification
- Frequency segmentation (one-time / occasional / loyal)
- Spend-tier segmentation (low / medium / high)
- Full RFM (Recency, Frequency, Monetary) scoring and segment labeling

---

## 5. Edge Case Handling

`scripts/test_edge_cases.py` verifies, independently of the main pipeline:

1. `order_items` rows referencing a non-existent `order_id` are removed during cleaning
2. `discount_percent > 100` is clipped during cleaning, and rejected outright by the database's `CHECK` constraint
3. `quantity = 0` rows are preserved and correctly contribute zero revenue
4. Future-dated orders are preserved (not silently dropped) and flagged in the data quality report
5. The CLI's `summary` report handles an empty result set gracefully (no crash, friendly message)
6. A minimal single-customer/single-order dataset loads and computes correct revenue
7. The CLI rejects invalid date strings and unrecognized `--report` values with clear errors and non-zero exit codes

The `report_cli.py` tool itself also handles:
- A missing database file (clear message, doesn't traceback)
- Database/connection errors (caught and reported)
- Invalid `--start`/`--end` dates or `--end` before `--start`
- Any `--report` value not in the supported list (enforced by `argparse` choices)

Run it with:
```bash
python scripts/test_edge_cases.py
```
Sample output is saved at `output/sample_reports/edge_case_test_results.txt`.

---

## 6. Repository Structure

```
ecommerce-analytics-system/
│── data/
│   ├── raw/                     # Step 1 output — messy generated CSVs
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   ├── orders.csv
│   │   └── order_items.csv
│   ├── cleaned/                 # Step 2 output — cleaned CSVs
│   │   ├── customers_clean.csv
│   │   ├── products_clean.csv
│   │   ├── orders_clean.csv
│   │   └── order_items_clean.csv
│   └── ecommerce.db             # Step 3 output — SQLite database
│── scripts/
│   ├── generate_data.py         # Step 1: dataset generation
│   ├── clean_data.py            # Step 2: cleaning + referential integrity checks
│   ├── load_db.py               # Step 3: schema creation + data load + verification
│   ├── report_cli.py            # Step 8: CLI reporting tool
│   └── test_edge_cases.py       # Step 9: edge-case test suite
│── sql/
│   ├── schema.sql                # PK/FK/CHECK constraints
│   ├── aggregations.sql          # Step 4: joins & aggregations
│   ├── window_functions.sql      # Step 5: window functions & CTEs
│   └── cohort_analysis.sql       # Steps 6-7: cohort, retention, RFM segmentation
│── output/
│   └── sample_reports/
│       ├── data_quality_report.txt
│       ├── revenue_and_top_customers.txt
│       ├── retention_report.txt
│       ├── rfm_report.txt
│       ├── monthly_summary_report.txt
│       └── edge_case_test_results.txt
│── README.md
```

---

## 7. Sample Output

A monthly summary report (`--report summary --start 2025-06-01 --end 2025-06-30`):

```
Monthly Summary Report
Period: 2025-06-01 to 2025-06-30  (30 day(s))
Previous period for comparison: 2025-05-02 to 2025-05-31
+------------------+------------------+-------------------+------------+
| Metric           |   Current Period |   Previous Period |   % Change |
+==================+==================+===================+============+
| Total Orders     |               90 |                99 |      -9.09 |
+------------------+------------------+-------------------+------------+
| Total Revenue    |      1.68018e+07 |       1.80234e+07 |      -6.78 |
+------------------+------------------+-------------------+------------+
| Unique Customers |               83 |                94 |     -11.70 |
+------------------+------------------+-------------------+------------+

Top 3 Products (by revenue)
+------------------+-----------+
| Product Name     |   Revenue |
+==================+===========+
| By Women         |    848315 |
+------------------+-----------+
| Top Decor        |    832432 |
+------------------+-----------+
| Because Footwear |    528513 |
+------------------+-----------+
```

More full-length sample outputs (revenue by category, top customers,
cohort retention, RFM segments, and the edge-case test run) are saved as
text files under `output/sample_reports/`.

---

## 8. Notes & Design Decisions

- **SQLite** was used as the target database for portability — the schema
  and queries use standard SQL and should port to PostgreSQL/MySQL with
  minor syntax changes (e.g. `strftime` → `TO_CHAR`/`DATE_FORMAT`).
- **Guest orders** (`customer_id IS NULL`) are intentionally kept rather
  than dropped, since in a real system unattributed orders are still valid
  business events — they're simply excluded from customer-level analytics
  via `WHERE customer_id IS NOT NULL`.
- **Returns** (`quantity < 0`) are kept in the base `order_items` table
  (not moved to a separate table) so that revenue formulas naturally net
  them out without special-casing every query.
- Random seeds are fixed (`Faker.seed(42)`, `random.seed(42)`) in
  `generate_data.py` so the dataset is reproducible across runs.
