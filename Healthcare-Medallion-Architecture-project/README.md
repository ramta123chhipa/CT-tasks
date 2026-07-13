# Healthcare & Hospital Management System — Medallion Architecture

End-to-end Bronze → Silver → Gold data pipeline built on **Azure Databricks**, **Azure Data Lake Storage Gen2**, **PySpark**, and **Delta Lake**.

> Built as part of the Celebal Technologies Data Engineering internship. Full write-up: [`Healthcare_Medallion_Implementation_Report.docx`](./Healthcare_Medallion_Implementation_Report.docx)

---

## Architecture

```
landing/ (raw CSVs)
   │
   ▼
BRONZE  →  bronze.patients, bronze.appointments, bronze.billing,
           bronze.doctors, bronze.treatments
   │  (cleanse, dedupe, PII mask, join)
   ▼
SILVER  →  silver.silver_patients, silver.silver_appointments,
           silver.silver_billing, silver.silver_doctors, silver.silver_treatments
   │  (aggregate into business KPIs)
   ▼
GOLD    →  gold.kpi_appointment_rates, gold.kpi_billing_accuracy,
           gold.kpi_claim_approval, gold.kpi_revenue_by_specialization,
           gold.kpi_doctor_workload
```

All pipeline runs are logged to `control.audit_log`; source configuration is metadata-driven via `control.metadata_config`.

## Notebooks

| # | Notebook | Layer | What it does |
|---|---|---|---|
| 00 | `00_setup_config` | Setup | Creates `control` database, `metadata_config` table (5 registered sources), `audit_log` table |
| 01 | `01_ingest_bronze` | Bronze | Metadata-driven CSV → Delta ingestion for all 5 sources, with audit columns |
| 02 | `02_silver_patients` | Silver | Dedup, null-filter, SHA-256 PII masking (contact_number, email, insurance_number) |
| 03 | `03_silver_appointments` | Silver | Joins to patients + doctors, derives `no_show_flag` / `cancelled_flag` |
| 04 | `04_silver_billing` | Silver | Validates charge amounts, standardizes payment status, joins to patients |
| 05 | `05_silver_doctors_treatments` | Silver | Dedup/cleanse doctors and treatments |
| 06 | `06_gold_kpis` | Gold | Computes 5 business KPIs (see below) |
| 07 | `07_audit_report` | Ops | Queries `control.audit_log` for pipeline run history and health summary |

## KPIs (Gold Layer)

| KPI | Table |
|---|---|
| Patient No-Show Rate | `gold.kpi_appointment_rates` |
| Appointment Cancellation Rate | `gold.kpi_appointment_rates` |
| Billing Accuracy Rate | `gold.kpi_billing_accuracy` |
| Insurance Claim Approval Rate | `gold.kpi_claim_approval` |
| Revenue by Doctor Specialization | `gold.kpi_revenue_by_specialization` |
| Doctor Appointment Workload | `gold.kpi_doctor_workload` |

Four KPIs from the original design (Average Length of Stay, HCAHPS Satisfaction Score, Medication Inventory Turnover, Patient Readmission Rate) were **not implemented** — they require admission/discharge timestamps, patient survey scores, and a medications dataset that were never part of the delivered source files. See the implementation report for full details.

## Source Data

| File | Rows | Notes |
|---|---|---|
| `patients.csv` | 50 | Patient master data |
| `appointments.csv` | 200 | Appointment records |
| `billing.csv` | 200 | Billing & payment records |
| `doctors.csv` | 10 | Doctor roster |
| `treatments.csv` | 200 | Treatment records |

## Setup

1. **Azure resources**: Resource Group → Storage Account (ADLS Gen2, hierarchical namespace **on**) → 4 containers (`landing`, `bronze`, `silver`, `gold`) → Databricks Workspace (Premium) → single-node cluster
2. **Secrets**: create a Databricks secret scope and store the storage account access key
   ```
   databricks secrets create-scope kv-scope
   databricks secrets put-secret kv-scope storage-key --string-value "<your-key>"
   ```
3. **Upload data**: place the 5 CSVs in the `landing` container
4. **Run notebooks in order**: `00` → `01` → `02`–`05` (any order) → `06` → `07`

Each notebook's first cell connects to storage:
```python
storage_account = "<your-storage-account-name>"
storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)
```

## Known Issues / Notes

- **Authentication**: the original plan (Service Principal + OAuth) hit a network-level `Failed to select a proxy` error on this cluster; the project uses Storage Account key auth via secret scope instead. See implementation report §2 and §8.
- **SCD Type 2**: not yet implemented on `silver_patients` (currently overwrite-based); flagged as a follow-up.
- **Unity Catalog**: `input_file_name()` is blocked under UC — use `F.col("_metadata.file_path")` instead.

## Tech Stack

Azure Databricks · Azure Data Lake Storage Gen2 · PySpark · Delta Lake · Databricks SQL · Unity Catalog
