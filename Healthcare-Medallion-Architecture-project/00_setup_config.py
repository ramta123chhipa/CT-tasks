# Databricks notebook source
from pyspark.sql.types import *
from pyspark.sql import functions as F

storage_account = "celebaldedata123"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

def path(container, filename=""):
    return f"abfss://{container}@{storage_account}.dfs.core.windows.net/{filename}"

# --- Databases banao ---
spark.sql("CREATE DATABASE IF NOT EXISTS control")
spark.sql("CREATE DATABASE IF NOT EXISTS bronze")
spark.sql("CREATE DATABASE IF NOT EXISTS silver")
spark.sql("CREATE DATABASE IF NOT EXISTS gold")

# --- Metadata Config table ---
metadata_schema = StructType([
    StructField("source_id", StringType()),
    StructField("source_name", StringType()),
    StructField("file_path", StringType()),
    StructField("file_format", StringType()),
    StructField("target_table", StringType()),
    StructField("primary_key", StringType()),
    StructField("active_flag", StringType()),
    StructField("load_type", StringType()),
])

sources = [
    ("SRC_001", "patients",    path("landing", "patients.csv"),    "csv", "bronze.patients",    "patient_id",    "Y", "FULL"),
    ("SRC_002", "appointments",path("landing", "appointments.csv"),"csv", "bronze.appointments","appointment_id","Y", "FULL"),
    ("SRC_003", "billing",     path("landing", "billing.csv"),     "csv", "bronze.billing",     "bill_id",    "Y", "FULL"),
    ("SRC_004", "doctors",     path("landing", "doctors.csv"),     "csv", "bronze.doctors",     "doctor_id",     "Y", "FULL"),
    ("SRC_005", "treatments",  path("landing", "treatments.csv"),  "csv", "bronze.treatments",  "treatment_id",  "Y", "FULL"),
]

df = spark.createDataFrame(sources, schema=metadata_schema)
df.write.format("delta").mode("overwrite").saveAsTable("control.metadata_config")

# --- Audit Log table ---
spark.sql("""
CREATE TABLE IF NOT EXISTS control.audit_log (
  audit_id STRING, batch_id STRING, source_name STRING, layer STRING,
  pipeline_start_time TIMESTAMP, pipeline_end_time TIMESTAMP,
  rows_read LONG, rows_written LONG, status STRING, error_message STRING,
  created_at TIMESTAMP
) USING DELTA
""")

print("Setup complete! Verify below:")
display(spark.table("control.metadata_config"))