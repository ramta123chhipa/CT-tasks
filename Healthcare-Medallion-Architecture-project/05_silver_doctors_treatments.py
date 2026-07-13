# Databricks notebook source
storage_account = "celebaldedata123"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)
from pyspark.sql import functions as F

# COMMAND ----------

silver_doctors = (spark.table("bronze.doctors")
    .dropDuplicates(["doctor_id"])
    .filter(F.col("doctor_id").isNotNull())
    .withColumn("_silver_load_timestamp", F.current_timestamp())
)
silver_doctors.write.format("delta").mode("overwrite").saveAsTable("silver.silver_doctors")
print(f"✅ silver_doctors: {silver_doctors.count()} rows")

# COMMAND ----------

silver_treatments = (spark.table("bronze.treatments")
    .dropDuplicates(["treatment_id"])
    .filter(F.col("treatment_id").isNotNull())
    .withColumn("_silver_load_timestamp", F.current_timestamp())
)
silver_treatments.write.format("delta").mode("overwrite").saveAsTable("silver.silver_treatments")
print(f"✅ silver_treatments: {silver_treatments.count()} rows")

# COMMAND ----------

