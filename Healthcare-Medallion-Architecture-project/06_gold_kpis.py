# Databricks notebook source
storage_account = "celebaldedata123"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)
spark.sql("CREATE DATABASE IF NOT EXISTS gold")
from pyspark.sql import functions as F

# COMMAND ----------

kpi_appointments = spark.sql("""
    SELECT
        current_date() AS report_date,
        COUNT(*) AS total_appointments,
        ROUND(SUM(no_show_flag) / COUNT(*) * 100, 2) AS no_show_rate_pct,
        ROUND(SUM(cancelled_flag) / COUNT(*) * 100, 2) AS cancellation_rate_pct
    FROM silver.silver_appointments
""")
kpi_appointments.write.format("delta").mode("overwrite").saveAsTable("gold.kpi_appointment_rates")
display(kpi_appointments)

# COMMAND ----------

kpi_billing_accuracy = spark.sql("""
    SELECT
        current_date() AS report_date,
        ROUND(SUM(CASE WHEN payment_status_clean != 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS billing_accuracy_pct,
        ROUND(SUM(CASE WHEN payment_status_clean = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS failed_transaction_pct
    FROM silver.silver_billing
""")
kpi_billing_accuracy.write.format("delta").mode("overwrite").saveAsTable("gold.kpi_billing_accuracy")
display(kpi_billing_accuracy)

# COMMAND ----------

kpi_claim_approval = spark.sql("""
    SELECT
        current_date() AS report_date,
        ROUND(SUM(CASE WHEN payment_method = 'Insurance' AND payment_status_clean = 'PAID' THEN 1 ELSE 0 END) * 100.0 /
              NULLIF(SUM(CASE WHEN payment_method = 'Insurance' THEN 1 ELSE 0 END), 0), 2) AS insurance_claim_approval_pct
    FROM silver.silver_billing
""")
kpi_claim_approval.write.format("delta").mode("overwrite").saveAsTable("gold.kpi_claim_approval")
display(kpi_claim_approval)

# COMMAND ----------

kpi_revenue_by_specialization = spark.sql("""
    SELECT
        current_date() AS report_date,
        d.specialization,
        COUNT(DISTINCT a.appointment_id) AS total_appointments,
        ROUND(SUM(b.amount), 2) AS total_revenue
    FROM silver.silver_appointments a
    JOIN bronze.doctors d ON a.doctor_id = d.doctor_id
    JOIN silver.silver_billing b ON a.patient_id = b.patient_id
    GROUP BY d.specialization
    ORDER BY total_revenue DESC
""")
kpi_revenue_by_specialization.write.format("delta").mode("overwrite").saveAsTable("gold.kpi_revenue_by_specialization")
display(kpi_revenue_by_specialization)

# COMMAND ----------

kpi_doctor_workload = spark.sql("""
    SELECT
        current_date() AS report_date,
        d.doctor_id,
        d.first_name,
        d.last_name,
        d.specialization,
        COUNT(a.appointment_id) AS total_appointments,
        ROUND(SUM(a.no_show_flag) * 100.0 / COUNT(*), 2) AS doctor_no_show_rate_pct
    FROM silver.silver_appointments a
    JOIN bronze.doctors d ON a.doctor_id = d.doctor_id
    GROUP BY d.doctor_id, d.first_name, d.last_name, d.specialization
    ORDER BY total_appointments DESC
""")
kpi_doctor_workload.write.format("delta").mode("overwrite").saveAsTable("gold.kpi_doctor_workload")
display(kpi_doctor_workload)

# COMMAND ----------

