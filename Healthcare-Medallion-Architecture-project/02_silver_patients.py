# Databricks notebook source
storage_account = "celebaldedata123"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)
spark.sql("CREATE DATABASE IF NOT EXISTS silver")
from pyspark.sql import functions as F

# COMMAND ----------

bronze_patients = spark.table("bronze.patients")

silver_patients = (bronze_patients
    .dropDuplicates(["patient_id"])
    .filter(F.col("patient_id").isNotNull())
    .withColumn("contact_number_masked", F.sha2(F.col("contact_number").cast("string"), 256))
    .withColumn("email_masked", F.sha2(F.col("email").cast("string"), 256))
    .withColumn("insurance_number_masked", F.sha2(F.col("insurance_number").cast("string"), 256))
    .drop("contact_number", "email", "insurance_number")
    .withColumn("_silver_load_timestamp", F.current_timestamp())
)

silver_patients.write.format("delta").mode("overwrite").saveAsTable("silver.silver_patients")
print(f"✅ silver_patients: {silver_patients.count()} rows, PII masked (contact_number, email, insurance_number)")
display(silver_patients.limit(5))

# COMMAND ----------

