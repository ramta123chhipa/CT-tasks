# Databricks notebook source
storage_account = "celebaldedata123"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)
from pyspark.sql import functions as F

# COMMAND ----------

silver_appointments = (spark.table("bronze.appointments")
    .filter(F.col("appointment_date").isNotNull())
    .join(spark.table("silver.silver_patients").select("patient_id"), "patient_id", "inner")
    .join(spark.table("bronze.doctors").select("doctor_id"), "doctor_id", "inner")
    .withColumn("no_show_flag", F.when(F.col("status") == "No-show", 1).otherwise(0))
    .withColumn("cancelled_flag", F.when(F.col("status") == "Cancelled", 1).otherwise(0))
    .withColumn("_silver_load_timestamp", F.current_timestamp())
)
silver_appointments.write.format("delta").mode("overwrite").saveAsTable("silver.silver_appointments")
print(f"✅ silver_appointments: {silver_appointments.count()} rows")
display(silver_appointments.limit(5))

# COMMAND ----------

