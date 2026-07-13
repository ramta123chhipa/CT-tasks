# Databricks notebook source
storage_account = "celebaldedata123"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# COMMAND ----------

print("=== Full Audit Log ===")
display(spark.table("control.audit_log").orderBy("created_at", ascending=False))

# COMMAND ----------

summary = spark.sql("""
    SELECT
        source_name,
        layer,
        status,
        rows_read,
        rows_written,
        ROUND((unix_timestamp(pipeline_end_time) - unix_timestamp(pipeline_start_time)), 2) AS duration_secs,
        created_at
    FROM control.audit_log
    ORDER BY created_at DESC
""")
display(summary)

# COMMAND ----------

health = spark.sql("""
    SELECT
        layer,
        COUNT(*) AS total_runs,
        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_runs,
        SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs,
        SUM(rows_written) AS total_rows_processed
    FROM control.audit_log
    GROUP BY layer
""")
print("=== Pipeline Health Summary ===")
display(health)

# COMMAND ----------

