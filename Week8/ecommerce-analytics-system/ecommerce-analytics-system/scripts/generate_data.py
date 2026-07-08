"""
generate_data.py
-----------------
Generates 4 raw CSV datasets for the E-Commerce Order Analytics System:
    - customers.csv
    - products.csv
    - orders.csv
    - order_items.csv

The data is intentionally messy (nulls, bad formats, duplicates, invalid
references) so that the cleaning step (clean_data.py) has real work to do.

Usage:
    python generate_data.py
Output:
    ../data/raw/customers.csv
    ../data/raw/products.csv
    ../data/raw/orders.csv
    ../data/raw/order_items.csv
"""

import csv
import os
import random
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
N_CUSTOMERS = 600
N_PRODUCTS = 150
N_ORDERS = 3000
N_ORDER_ITEMS = 6500

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]
ORDER_STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
CATEGORIES = {
    "Electronics": ["Mobiles", "Laptops", "Accessories", "Cameras"],
    "Clothing": ["Men", "Women", "Kids", "Footwear"],
    "Home": ["Kitchen", "Furniture", "Decor", "Appliances"],
    "Books": ["Fiction", "Non-Fiction", "Academic", "Comics"],
}
REGION_CODES = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]


def random_date(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


# ---------------------------------------------------------------------------
# 1. customers.csv
# ---------------------------------------------------------------------------
def generate_customers():
    rows = []
    reg_start = datetime(2022, 1, 1)
    reg_end = datetime(2026, 6, 1)

    for cid in range(1, N_CUSTOMERS + 1):
        name = fake.name()
        email = fake.email()

        # 2% invalid emails (missing @ or domain)
        if random.random() < 0.02:
            bad_type = random.choice(["no_at", "no_domain"])
            if bad_type == "no_at":
                email = email.replace("@", "")
            else:
                email = email.split("@")[0] + "@"

        reg_date = random_date(reg_start, reg_end)

        rows.append(
            {
                "customer_id": cid,
                "customer_name": name,
                "email": email,
                "registration_date": reg_date.strftime("%Y-%m-%d %H:%M:%S"),
                "customer_type": random.choices(
                    CUSTOMER_TYPES, weights=[0.6, 0.3, 0.1]
                )[0],
            }
        )

    # introduce a handful of duplicate customer rows (same customer_id re-inserted)
    for _ in range(8):
        dup = dict(random.choice(rows))
        rows.append(dup)

    with open(os.path.join(RAW_DIR, "customers.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["customer_id", "customer_name", "email", "registration_date", "customer_type"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


# ---------------------------------------------------------------------------
# 2. products.csv
# ---------------------------------------------------------------------------
def generate_products():
    rows = []
    for pid in range(1, N_PRODUCTS + 1):
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(CATEGORIES[category])
        name = f"{fake.word().capitalize()} {subcategory[:-1] if subcategory.endswith('s') else subcategory}"

        # messy product names: extra spaces / mixed case for ~15% of rows
        if random.random() < 0.15:
            messy_variant = random.choice(["upper", "lower", "spaces"])
            if messy_variant == "upper":
                name = name.upper()
            elif messy_variant == "lower":
                name = name.lower()
            else:
                name = f"   {name}   "

        cost_price = round(random.uniform(50, 50000), 2)

        rows.append(
            {
                "product_id": pid,
                "product_name": name,
                "category": category,
                "subcategory": subcategory,
                "cost_price": cost_price,
            }
        )

    with open(os.path.join(RAW_DIR, "products.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["product_id", "product_name", "category", "subcategory", "cost_price"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


# ---------------------------------------------------------------------------
# 3. orders.csv
# ---------------------------------------------------------------------------
def generate_orders(customers):
    rows = []
    order_start = datetime(2024, 1, 1)
    order_end = datetime(2026, 6, 30)
    customer_ids = [c["customer_id"] for c in customers]

    for oid in range(1, N_ORDERS + 1):
        # 5% missing customer_id
        if random.random() < 0.05:
            customer_id = ""  # empty -> NULL
        else:
            customer_id = random.choice(customer_ids)

        order_dt = random_date(order_start, order_end)

        # ~1% of orders have a future order_date (edge case for testing)
        if random.random() < 0.01:
            order_dt = datetime.now() + timedelta(days=random.randint(1, 60))

        # Most dates in correct format YYYY-MM-DD HH:MM:SS,
        # ~8% in wrong format DD-MM-YYYY (no time component)
        if random.random() < 0.08:
            date_str = order_dt.strftime("%d-%m-%Y")
        else:
            date_str = order_dt.strftime("%Y-%m-%d %H:%M:%S")

        rows.append(
            {
                "order_id": oid,
                "customer_id": customer_id,
                "order_date": date_str,
                "status": random.choices(
                    ORDER_STATUSES, weights=[0.15, 0.2, 0.45, 0.1, 0.1]
                )[0],
                "region_code": random.choice(REGION_CODES),
                "_dt": order_dt,  # kept internally to build valid order_items later
            }
        )

    with open(os.path.join(RAW_DIR, "orders.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["order_id", "customer_id", "order_date", "status", "region_code"]
        )
        writer.writeheader()
        for r in rows:
            writer.writerow({k: v for k, v in r.items() if k != "_dt"})

    return rows


# ---------------------------------------------------------------------------
# 4. order_items.csv
# ---------------------------------------------------------------------------
def generate_order_items(orders, products):
    rows = []
    valid_order_ids = [o["order_id"] for o in orders]
    product_ids = [p["product_id"] for p in products]
    product_price = {p["product_id"]: p["cost_price"] for p in products}

    for iid in range(1, N_ORDER_ITEMS + 1):
        # ~1.5% reference a non-existent order_id -> referential integrity issue
        if random.random() < 0.015:
            order_id = max(valid_order_ids) + random.randint(1, 500)
        else:
            order_id = random.choice(valid_order_ids)

        product_id = random.choice(product_ids)
        base_price = product_price[product_id]
        unit_price = round(base_price * random.uniform(1.1, 1.8), 2)  # markup over cost

        quantity = random.randint(1, 5)

        # 3% negative quantity (returns)
        if random.random() < 0.03:
            quantity = -quantity

        # small % quantity = 0 (edge case)
        if random.random() < 0.005:
            quantity = 0

        discount_percent = round(random.uniform(0, 40), 1)
        # rare invalid discount > 100 (edge case for testing)
        if random.random() < 0.003:
            discount_percent = round(random.uniform(101, 150), 1)

        rows.append(
            {
                "item_id": iid,
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_percent": discount_percent,
            }
        )

    with open(os.path.join(RAW_DIR, "order_items.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


def main():
    print("Generating customers.csv ...")
    customers = generate_customers()
    print(f"  -> {len(customers)} rows")

    print("Generating products.csv ...")
    products = generate_products()
    print(f"  -> {len(products)} rows")

    print("Generating orders.csv ...")
    orders = generate_orders(customers)
    print(f"  -> {len(orders)} rows")

    print("Generating order_items.csv ...")
    order_items = generate_order_items(orders, products)
    print(f"  -> {len(order_items)} rows")

    print(f"\nAll raw CSV files written to: {os.path.abspath(RAW_DIR)}")


if __name__ == "__main__":
    main()
