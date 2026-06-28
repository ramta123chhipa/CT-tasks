# Azure End-to-End Data Pipeline using Azure Data Factory

## Objective
The objective of this project is to understand Azure cloud concepts and build an end-to-end data pipeline using Azure Storage Account and Azure Data Factory (ADF).

---

## Project Overview
This project demonstrates how to create a simple data pipeline in Azure that moves data from **Azure Blob Storage** to a destination using **Azure Data Factory**, along with metadata validation and monitoring.

---

## Architecture
**Blob Storage → Azure Data Factory Pipeline → Destination Dataset**

---

## Steps Followed

### 1. Resource Group
- Created a Resource Group in Azure Portal to manage all resources.

### 2. Storage Account Setup
- Created an Azure Storage Account.
- Created a Blob Container.
- Uploaded a sample CSV file into the container.

### 3. Azure Data Factory Setup
- Created an Azure Data Factory instance.
- Explored ADF UI:
  - Author
  - Monitor
  - Manage

### 4. Linked Services
- Created Linked Service to connect ADF with Blob Storage.

### 5. Datasets
- Defined source dataset (Blob Storage CSV file).
- Defined destination dataset.

### 6. Pipeline Development
- Used **Get Metadata Activity** to retrieve file information.
- Used **Copy Data Activity** to move data from source to destination.
- Configured source and sink properly.

### 7. Execution & Monitoring
- Executed pipeline using **Debug / Trigger Now**.
- Monitored pipeline execution in ADF Monitor tab.

### 8. IAM Roles
- Assigned appropriate roles:
  - Reader
  - Contributor
- Ensured secure access between ADF and Storage Account.

---

## Output
- Resource Group created successfully
- Storage Account and Blob Container configured
- Azure Data Factory pipeline built and executed
- Data successfully transferred from Blob Storage to destination
- Metadata validation completed using Get Metadata activity

---

## Key Learnings
- Basics of Azure cloud infrastructure
- Working with Azure Storage Account and Blob Storage
- Creating and managing pipelines in Azure Data Factory
- Data movement and transformation concepts
- Role-based access control (IAM) in Azure
- Monitoring and debugging data pipelines

---

## Tools Used
- Microsoft Azure Portal
- Azure Storage Account (Blob Storage)
- Azure Data Factory
- CSV dataset

---
