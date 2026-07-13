# Databricks notebook source
import uuid, datetime
from pyspark.sql import functions as F

storage_account = "celebaldedata123"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

batch_id = str(uuid.uuid4())

def ingest_source(row):
    start = datetime.datetime.now()
    try:
        raw_df = (spark.read.format(row.file_format)
                  .option("header", True).option("inferSchema", True)
                  .load(row.file_path))
        rows_read = raw_df.count()

        bronze_df = (raw_df
            .withColumn("_ingestion_timestamp", F.current_timestamp())
            .withColumn("_source_file_name", F.col("_metadata.file_path"))
            .withColumn("_batch_id", F.lit(batch_id))
            .withColumn("_ingestion_date", F.current_date())
        )

        (bronze_df.write.format("delta").mode("overwrite")
            .option("mergeSchema", "true")
            .saveAsTable(row.target_table))

        status, error = "SUCCESS", None
        print(f"✅ {row.source_name}: {rows_read} rows loaded into {row.target_table}")
    except Exception as e:
        rows_read, status, error = 0, "FAILED", str(e)
        print(f"❌ {row.source_name}: {error}")

    end = datetime.datetime.now()
    log_row = [(str(uuid.uuid4()), batch_id, row.source_name, "BRONZE", start, end,
                rows_read, rows_read, status, error, datetime.datetime.now())]
    spark.createDataFrame(log_row, schema=spark.table("control.audit_log").schema)\
        .write.format("delta").mode("append").saveAsTable("control.audit_log")

active_sources = spark.table("control.metadata_config").filter("active_flag = 'Y'").collect()
for row in active_sources:
    ingest_source(row)

print("\n--- Audit Log ---")
display(spark.table("control.audit_log").filter(f"batch_id = '{batch_id}'"))

# COMMAND ----------

