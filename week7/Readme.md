# Delta Lake MERGE Assignment - Week 7

## Objective
Perform incremental data processing using Delta Lake's MERGE (upsert) operation on the Superstore dataset.

## Steps
1. Loaded raw CSV into Spark DataFrame
2. Cleaned data (removed duplicates, renamed columns to remove spaces)
3. Saved cleaned data as a Delta table
4. Created a simulated incremental dataset (2 updates + 2 new inserts)
5. Applied MERGE operation using Row_ID as the join key
6. Validated results (row count, duplicate check, updated/inserted records)

## Tech Stack
- PySpark 3.5.0
- Delta Lake 3.1.0
- Python 3.11

## Key Learning
Delta Lake's MERGE allows atomic upsert operations — updating existing records and inserting new ones in a single operation, unlike traditional overwrite-based approaches.