# Databricks notebook source
key = dbutils.secrets.get("kv-scope", "storage-key").strip()
print("Length after strip:", len(key))
print("First 10:", key[:10])
print("Last 10:", key[-10:])
print("Has spaces:", " " in key)
print("Has newlines:", "\n" in key)

# COMMAND ----------

storage_account = "celebaldedata123"

storage_key = dbutils.secrets.get("kv-scope", "storage-key").strip()
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# Test: landing container ki files list karo
files = dbutils.fs.ls(f"abfss://landing@{storage_account}.dfs.core.windows.net/")
for f in files:
    print(f.name)

# COMMAND ----------

