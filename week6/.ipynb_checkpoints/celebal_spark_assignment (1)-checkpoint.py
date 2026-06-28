"""

  CELEBAL INTERNSHIP ASSIGNMENT - Apache Spark Fundamentals
  PySpark: Data Cleaning, Transformation & Aggregation

"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType,
    IntegerType, DoubleType, LongType
)

#  Initialize Spark Session
print("\n" + "="*60)
print("  STEP 0: Initializing SparkSession")
print("="*60)

spark = SparkSession.builder \
    .appName("CelebalInternshipAssignment") \
    .master("local[*]") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print(" SparkSession created successfully!")
print(f"   Spark Version : {spark.version}")
print(f"   App Name      : {spark.sparkContext.appName}")
print(f"   Master        : {spark.sparkContext.master}")



#  MapReduce vs Spark – Key Concepts

print("\n" + "="*60)
print("  STEP 1: MapReduce Limitations & Spark Advantages")
print("="*60)
print("""
 MapReduce Limitations:
    Disk I/O after every Map & Reduce step
    No in-memory caching — data written to HDFS each time
    High latency — bad for iterative algorithms (ML, Graph)
    Two-stage only (Map → Reduce), complex pipelines need many jobs
   No native SQL / streaming support

 Apache Spark Advantages:
   ✔ In-memory processing — up to 100x faster than MapReduce
   ✔ DAG (Directed Acyclic Graph) execution engine
   ✔ Lazy evaluation — optimises entire pipeline before running
   ✔ Rich APIs: DataFrames, SQL, Streaming, MLlib, GraphX
   ✔ Single unified engine for batch + streaming + ML
   ✔ DataFrame immutability ensures fault tolerance
""")



#  Create Sample Dataset

print("="*60)
print("  STEP 2: Creating Sample Dataset")
print("="*60)

# Raw data with intentional issues (duplicates, nulls, wrong types)
raw_data = [
    (1,  "Alice",   29, "Electronics", "North", 1500.50, "2024-01-10"),
    (2,  "Bob",     35, "Clothing",    "South", 800.00,  "2024-01-11"),
    (3,  "Charlie", 17, "Electronics", "East",  200.00,  "2024-01-12"),  # under 18
    (4,  "Diana",   42, "Furniture",   "West",  3200.75, "2024-01-13"),
    (5,  "Eve",     None,"Clothing",   "North", 450.00,  "2024-01-14"),  # null age
    (6,  "Frank",   28, None,          "South", 600.00,  "2024-01-15"),  # null category
    (7,  "Grace",   33, "Electronics", "East",  None,    "2024-01-16"),  # null amount
    (8,  "Hank",    55, "Furniture",   None,    1800.00, "2024-01-17"),  # null region
    (9,  "Ivy",     23, "Clothing",    "West",  320.00,  "2024-01-18"),
    (10, "Jack",    31, "Electronics", "North", 2100.00, "2024-01-19"),
    (2,  "Bob",     35, "Clothing",    "South", 800.00,  "2024-01-11"),  # duplicate
    (11, "Karen",   45, "Furniture",   "East",  4500.00, "2024-01-20"),
    (12, "Leo",     19, "Electronics", "South", 950.00,  "2024-01-21"),
    (13, "Mona",    38, "Clothing",    "West",  670.00,  "2024-01-22"),
    (14, "Nate",    62, "Furniture",   "North", 2800.00, "2024-01-23"),
    (15, "Olivia",  27, "Electronics", "East",  1350.00, "2024-01-24"),
    (1,  "Alice",   29, "Electronics", "North", 1500.50, "2024-01-10"),  # duplicate
    (16, "Paul",    34, "Clothing",    "South", 530.00,  "2024-01-25"),
    (17, "Quinn",   None,"Furniture",  "West",  2200.00, "2024-01-26"),  # null age
    (18, "Rose",    41, "Electronics", "North", 1750.00, "2024-01-27"),
    (19, "Sam",     26, "Clothing",    "East",  410.00,  "2024-01-28"),
    (20, "Tina",    50, "Furniture",   "South", 3800.00, "2024-01-29"),
]

schema = StructType([
    StructField("customer_id",  IntegerType(), True),
    StructField("name",         StringType(),  True),
    StructField("age",          IntegerType(), True),
    StructField("category",     StringType(),  True),
    StructField("region",       StringType(),  True),
    StructField("amount",       DoubleType(),  True),
    StructField("sale_date",    StringType(),  True),
])

raw_df = spark.createDataFrame(raw_data, schema=schema)

print(f"📊 Raw Dataset: {raw_df.count()} rows × {len(raw_df.columns)} columns")
print("\n📋 Raw Data Schema:")
raw_df.printSchema()
print("📋 First 10 rows of Raw Data:")
raw_df.show(10, truncate=False)



# : Data Cleaning – Remove Duplicates

print("="*60)
print("  STEP 3: Data Cleaning – Removing Duplicates")
print("="*60)

before = raw_df.count()
deduped_df = raw_df.dropDuplicates()
after = deduped_df.count()

print(f"   Rows before dedup : {before}")
print(f"   Rows after dedup  : {after}")
print(f"   Duplicates removed: {before - after}")
deduped_df.show(truncate=False)


#  Null Values

print("="*60)
print("  STEP 4: Data Cleaning – Handling Null Values")
print("="*60)

# Count nulls per column
print("🔍 Null count per column:")
null_counts = deduped_df.select([
    F.count(F.when(F.col(c).isNull(), c)).alias(c)
    for c in deduped_df.columns
])
null_counts.show()



median_age = deduped_df.approxQuantile("age", [0.5], 0.01)[0]
print(f"   Median age used for imputation: {median_age}")

cleaned_df = (deduped_df
    .fillna({"age": int(median_age), "category": "Unknown", "region": "Unknown"})
    .filter(F.col("amount").isNotNull())          # drop rows where amount is null
    .filter(F.col("customer_id").isNotNull())
)

print(f"\n   Rows after null handling: {cleaned_df.count()}")
print("Cleaned DataFrame:")
cleaned_df.show(truncate=False)



# Schema Modification – Cast & Rename

print("="*60)
print("  STEP 5: Schema Modification – Casting & Renaming")
print("="*60)

transformed_df = (cleaned_df
    .withColumn("sale_date",    F.to_date(F.col("sale_date"), "yyyy-MM-dd"))
    .withColumn("amount",       F.col("amount").cast(DoubleType()))
    .withColumnRenamed("amount", "sale_amount")
    .withColumn("amount_inr",   F.round(F.col("sale_amount") * 83.5, 2))  # USD → INR
    .withColumn("age_group",
        F.when(F.col("age") < 25, "Youth")
         .when(F.col("age") < 40, "Adult")
         .when(F.col("age") < 60, "Middle-Aged")
         .otherwise("Senior"))
)

print(" Transformed Schema:")
transformed_df.printSchema()
print(" Transformed Data (with INR & Age Group):")
transformed_df.show(truncate=False)



#  Filtering Conditions

print("="*60)
print("  STEP 6: Filtering – Age Range, Category, Region")
print("="*60)

# Filter 1: Age 18–60
adults_df = transformed_df.filter((F.col("age") >= 18) & (F.col("age") <= 60))
print(f"Filter 1 – Age 18–60: {adults_df.count()} rows")
adults_df.show(truncate=False)

# Filter 2: Electronics category
electronics_df = transformed_df.filter(F.col("category") == "Electronics")
print(f"\nFilter 2 – Category = Electronics: {electronics_df.count()} rows")
electronics_df.show(truncate=False)

# Filter 3: North or East region
north_east_df = transformed_df.filter(F.col("region").isin("North", "East"))
print(f"\nFilter 3 – Region in (North, East): {north_east_df.count()} rows")
north_east_df.show(truncate=False)

# Filter 4: High-value sales > 1000
high_value_df = transformed_df.filter(F.col("sale_amount") > 1000)
print(f"\nFilter 4 – Sale Amount > 1000: {high_value_df.count()} rows")
high_value_df.show(truncate=False)


#  Aggregation Functions

print("="*60)
print("  STEP 7: Aggregation – count, sum, avg, min, max")
print("="*60)

overall_agg = transformed_df.agg(
    F.count("customer_id").alias("total_customers"),
    F.sum("sale_amount").alias("total_sales"),
    F.round(F.avg("sale_amount"), 2).alias("avg_sale"),
    F.min("sale_amount").alias("min_sale"),
    F.max("sale_amount").alias("max_sale"),
    F.round(F.avg("age"), 1).alias("avg_age"),
)

print("Overall Aggregation Results:")
overall_agg.show()



#  GroupBy Aggregation

print("="*60)
print("GroupBy Aggregation")
print("="*60)

# Group by Category
print("Sales by Category:")
category_agg = (transformed_df
    .groupBy("category")
    .agg(
        F.count("customer_id").alias("num_customers"),
        F.round(F.sum("sale_amount"), 2).alias("total_sales"),
        F.round(F.avg("sale_amount"), 2).alias("avg_sale"),
        F.min("sale_amount").alias("min_sale"),
        F.max("sale_amount").alias("max_sale"),
    )
    .orderBy(F.desc("total_sales"))
)
category_agg.show()

# Group by Region
print("Sales by Region:")
region_agg = (transformed_df
    .groupBy("region")
    .agg(
        F.count("customer_id").alias("num_customers"),
        F.round(F.sum("sale_amount"), 2).alias("total_sales"),
        F.round(F.avg("sale_amount"), 2).alias("avg_sale"),
    )
    .orderBy(F.desc("total_sales"))
)
region_agg.show()

# Group by Category + Region (WIDE TRANSFORMATION – triggers shuffle)
print("Sales by Category × Region (Wide Transformation / Shuffle):")
cat_region_agg = (transformed_df
    .groupBy("category", "region")
    .agg(
        F.count("customer_id").alias("num_customers"),
        F.round(F.sum("sale_amount"), 2).alias("total_sales"),
    )
    .orderBy("category", "region")
)
cat_region_agg.show(30)

# Group by Age Group
print("Sales by Age Group:")
age_group_agg = (transformed_df
    .groupBy("age_group")
    .agg(
        F.count("customer_id").alias("num_customers"),
        F.round(F.avg("sale_amount"), 2).alias("avg_sale"),
        F.round(F.sum("sale_amount"), 2).alias("total_sales"),
    )
    .orderBy("age_group")
)
age_group_agg.show()


# ─────────────────────────────────────────────
# STEP 9: HAVING equivalent (filter after groupBy)
# ─────────────────────────────────────────────
print("="*60)
print("  STEP 9: HAVING Clause Equivalent on Aggregated Results")
print("="*60)

# Categories with total_sales > 3000
high_revenue_cats = (transformed_df
    .groupBy("category")
    .agg(F.round(F.sum("sale_amount"), 2).alias("total_sales"))
    .filter(F.col("total_sales") > 3000)
    .orderBy(F.desc("total_sales"))
)
print("Categories with total sales > 3000:")
high_revenue_cats.show()

# Regions where avg sale > 1200
high_avg_regions = (transformed_df
    .groupBy("region")
    .agg(F.round(F.avg("sale_amount"), 2).alias("avg_sale"))
    .filter(F.col("avg_sale") > 1200)
    .orderBy(F.desc("avg_sale"))
)
print("Regions where avg sale > 1200:")
high_avg_regions.show()



# Wide vs Narrow Transformations

print("="*60)
print("  STEP 10: Wide vs Narrow Transformations Explained")
print("="*60)
print("""
 NARROW TRANSFORMATIONS (no shuffle – fast):
   • filter()   – keeps rows from same partition
   • select()   – column projection, same partition
   • map/withColumn() – row-wise, same partition
   • union()    – combine same-schema DFs

 WIDE TRANSFORMATIONS (shuffle – slower, network I/O):
   • groupBy()  – rows with same key → same partition
   • join()     – matching keys go to same partition
   • distinct() – deduplicate across all partitions
   • orderBy()  – global sort requires full data movement
   • repartition() – explicit data redistribution

 In our pipeline:
   • dropDuplicates()  → WIDE (shuffle to detect dupes)
   • groupBy("category").agg() → WIDE (shuffle by key)
   • filter(age > 18)  → NARROW (per-partition)
   • withColumn(...)   → NARROW (row-wise transform)
""")



# Spark SQL Alternative

print("="*60)
print("  STEP 11: Spark SQL – Equivalent Queries")
print("="*60)

transformed_df.createOrReplaceTempView("sales")

sql_result = spark.sql("""
    SELECT 
        category,
        region,
        COUNT(customer_id)         AS num_customers,
        ROUND(SUM(sale_amount), 2) AS total_sales,
        ROUND(AVG(sale_amount), 2) AS avg_sale,
        MIN(sale_amount)           AS min_sale,
        MAX(sale_amount)           AS max_sale
    FROM sales
    WHERE age BETWEEN 18 AND 60
      AND category != 'Unknown'
    GROUP BY category, region
    HAVING SUM(sale_amount) > 500
    ORDER BY total_sales DESC
""")

print("Spark SQL Result (Category × Region, Age 18–60, Total > 500):")
sql_result.show(30)



# Complete Data Processing Pipeline

print("="*60)
print("  STEP 12: Complete End-to-End Pipeline Summary")
print("="*60)

final_pipeline = (
    # 1. Load raw data (already done)
    raw_df
    # 2. Remove duplicates (WIDE)
    .dropDuplicates()
    # 3. Fill nulls for categorical columns
    .fillna({"age": 33, "category": "Unknown", "region": "Unknown"})
    # 4. Drop rows with null amount
    .filter(F.col("amount").isNotNull())
    # 5. Cast sale_date to DateType
    .withColumn("sale_date", F.to_date(F.col("sale_date"), "yyyy-MM-dd"))
    # 6. Rename amount
    .withColumnRenamed("amount", "sale_amount")
    # 7. Add derived columns
    .withColumn("amount_inr", F.round(F.col("sale_amount") * 83.5, 2))
    .withColumn("age_group",
        F.when(F.col("age") < 25, "Youth")
         .when(F.col("age") < 40, "Adult")
         .when(F.col("age") < 60, "Middle-Aged")
         .otherwise("Senior"))
    # 8. Filter valid age range
    .filter((F.col("age") >= 18) & (F.col("age") <= 65))
    # 9. Cache before multiple aggregations (performance tip)
    .cache()
)

print(f"Final pipeline produced {final_pipeline.count()} clean rows\n")
print("Final Clean Dataset:")
final_pipeline.show(truncate=False)

print("\nFinal Aggregation - Full Report:")
final_report = (
    final_pipeline
    .groupBy("category", "region", "age_group")
    .agg(
        F.count("customer_id").alias("customers"),
        F.round(F.sum("sale_amount"), 2).alias("total_usd"),
        F.round(F.avg("sale_amount"), 2).alias("avg_usd"),
        F.round(F.sum("amount_inr"), 2).alias("total_inr"),
    )
    .orderBy(F.desc("total_usd"))
)
final_report.show(50, truncate=False)


print("Assignment Complete! All steps executed successfully.")
spark.stop()
