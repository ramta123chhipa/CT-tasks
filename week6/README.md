# Week 6 — Apache Spark Fundamentals
**Celebal Technologies Internship Assignment**

---

## 📌 Objective

Understand Spark architecture and perform efficient data processing using transformations, filtering, schema handling, and optimized file formats.

---

## 🛠️ Tech Stack

| Tool | Version |
|------|---------|
| Python | 3.x |
| PySpark | 4.1.2 |
| JDK | 11 |
| Jupyter Notebook | Latest |
| pandas | Latest |
| pyarrow / fastparquet | Latest |

---

## 📁 Project Structure

```
week6/
├── pyspark/              # Virtual environment
├── output/
│   └── sales_data.csv    # Processed output file
├── Untitled.ipynb        # Main Jupyter Notebook
└── README.md             # This file
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites
- JDK 11 installed and `JAVA_HOME` set
- Python virtual environment created

### 2. Activate Virtual Environment
```bash
cd celebal-Technologies\week6\pyspark
Scripts\activate
```

### 3. Install Dependencies
```bash
pip install pyspark
pip install jupyter
pip install pandas
pip install pyarrow
pip install fastparquet
```

### 4. Start Jupyter Notebook
```bash
jupyter notebook
```

### 5. Set Environment Variables (Cell 1 of Notebook)
```python
import os, sys
os.environ["PYSPARK_PYTHON"] = r"path\to\pyspark\Scripts\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"path\to\pyspark\Scripts\python.exe"
os.environ["HADOOP_HOME"] = r"C:\hadoop"
```

---

## 📋 Tasks Completed

### 1. Spark Architecture
- **Driver**: Coordinates the job, builds DAG, schedules tasks
- **Cluster Manager**: Allocates resources (used `local[*]` mode)
- **Executors**: Run actual tasks on partitions

### 2. Lazy Evaluation & DAG
- All transformations (`filter`, `select`, `withColumn`) are lazy
- Execution triggered only on Actions (`show()`, `count()`, `cache()`)
- Catalyst Optimizer builds optimized execution plan

### 3. Sample Dataset
- 22 raw rows with intentional nulls and duplicates
- Schema: `customer_id`, `name`, `age`, `category`, `region`, `amount`

### 4. Data Cleaning
- Removed **2 duplicate rows** using `dropDuplicates()`
- Handled nulls: `age` → median imputation, `category/region` → "Unknown"
- Dropped rows where `amount` is null

### 5. Schema Modification
- Renamed `amount` → `sale_amount`
- Cast `sale_amount` to `DoubleType`
- Added `amount_inr` column (USD × 83.5)
- Added `age_group` column (Youth / Adult / Middle-Aged / Senior)

### 6. Filtering
- Age range: 18–60
- Category: Electronics only
- Region: North or East
- High value: sale_amount > 1000

### 7. Aggregation
- `count`, `sum`, `avg`, `min`, `max` on overall dataset
- `groupBy` on category, region, and age_group
- HAVING equivalent using `.filter()` after `.agg()`

### 8. Spark SQL
- Registered DataFrame as temp view using `createOrReplaceTempView()`
- Ran SQL queries with `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`

### 9. Wide vs Narrow Transformations
| Type | Examples | Shuffle? |
|------|----------|----------|
| Narrow | `filter`, `select`, `withColumn` | ❌ No |
| Wide | `groupBy`, `dropDuplicates`, `orderBy` | ✅ Yes |

### 10. File Formats
| Format | Type | Schema | Compression |
|--------|------|--------|-------------|
| CSV | Row-based | No | No |
| Parquet | Columnar | Yes | Yes |

### 11. Data Pipeline
```
Raw Data (22 rows)
    ↓ dropDuplicates()      → 20 rows
    ↓ fillna() + filter()   → 19 rows
    ↓ withColumn() × 3      → schema enriched
    ↓ age filter (18–65)    → 18 rows
    ↓ cache()               → stored in memory
    ↓ save to CSV           → output/sales_data.csv
```

### 12. Best Practices Followed
- Used `show(n)` instead of `collect()` for previews
- Applied `cache()` before multiple aggregations
- Used `setLogLevel("ERROR")` to suppress verbose logs
- Filters applied early in pipeline to reduce data volume

---

## 📊 Key Insights

- **Furniture** category had highest avg sale amount — premium segment
- **North region** led in total revenue
- **Middle-Aged customers (40–59)** spent the most overall
- Only **2 shuffle operations** in entire pipeline — kept processing efficient
- `cache()` prevented recomputation across multiple aggregation steps

---

## ▶️ How to Run

1. Open `Untitled.ipynb` in Jupyter
2. Run cells in order from top to bottom
3. Output CSV will be saved at `week6/output/sales_data.csv`

---

## 👩‍💻 Author

**Celebal Technologies Internship — Week 6**
