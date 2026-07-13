# Databricks notebook source
storage_account = "celebaldedata123"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)
from pyspark.sql import functions as F

# COMMAND ----------

silver_billing = (spark.table("bronze.billing")
    .filter(F.col("amount") > 0)
    .withColumn("payment_status_clean", F.upper(F.trim(F.col("payment_status"))))
    .join(spark.table("silver.silver_patients").select("patient_id"), "patient_id", "inner")
    .withColumn("_silver_load_timestamp", F.current_timestamp())
)
silver_billing.write.format("delta").mode("overwrite").saveAsTable("silver.silver_billing")
print(f"✅ silver_billing: {silver_billing.count()} rows")
display(silver_billing.limit(5))

# COMMAND ----------

