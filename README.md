## Architecture Overview

1. **Blob Trigger Function**: Watches the `images-input` container for new uploads and starts an orchestration.
2. **Orchestrator Function**: Coordinates a sequence of activities (e.g., metadata extraction, image analysis).
3. **Activity Functions**: Perform discrete work items (e.g., `GetImageMetadata`, `ProcessImage`).
4. **Durable Function Tables**: Azure Table Storage tables to track instance states and history.

---



## Code Structure

```
├── BlobTriggerClient/         # Entry point for blob-triggered orchestration
│   └── function.json
│   └── __init__.py
├── OrchestratorFunction/      # Orchestration logic
│   └── function.json
│   └── __init__.py
├── ExtractMetadata/          # Activity: extract metadata
│   └── function.json
│   └── __init__.py
├── StoreMetadata/              # Activity: image scanning
│   └── function.json
│   └── __init__.py
├── host.json
├── requirements.txt
└── README.md
```

---
## Azure Resources

### Resource Provisioning


### Resource Group  
**Type:** Azure Resource Group  
**Name:** `image-metadata-rg`  
**Location:** `East US`  
**What to create:**  
- Logical container for all project resources.

---

### Storage Account  
**Type:** Storage Account (StorageV2)  
**Name:** `imagemetadatastorage`  
**Resource Group:** `image-metadata-rg`  
**Location:** `East US`  
**SKU:** `Standard_LRS`  
**Kind:** `StorageV2`  
**What to create:**  
- Blob container named `images-input` (no public access).  
- This container will raise the blob trigger when `.jpg`, `.png`, or `.gif` files arrive.

---

### Function App  
**Type:** Azure Function App (Consumption)  
**Name:** `imagemetadatafuncapp`  
**Resource Group:** `image-metadata-rg`  
**Location:** `East US`  
**Runtime:** Python 3.11  
**Plan:** Consumption (Serverless)  
**Storage Account:** `imagemetadatastorage`  
**App Settings to configure:**  
- `AzureWebJobsStorage` → connection string for `imagemetadatastorage`  
- `FUNCTIONS_WORKER_RUNTIME` → `python`  
- `WEBSITE_RUN_FROM_PACKAGE` → URL or path to your deployment package  
- `SqlConnectionString` → connection string for your Azure SQL DB  

---

### Azure SQL Server  
**Type:** Azure SQL Server  
**Name:** `imagemetadata-sqlsrv`  
**Resource Group:** `image-metadata-rg`  
**Location:** `East US`  
**Admin login:** `<yourAdminUser>`  
**Admin password:** `<yourStrongPassword>`  
**What to create:**  
- Firewall rule `AllowAzureServices` to permit Function App outbound traffic.

---

### Azure SQL Database  
**Type:** SQL Database  
**Name:** `imagemetadata-db`  
**Server:** `imagemetadata-sqlsrv`  
**Resource Group:** `image-metadata-rg`  
**Location:** `East US`  
**Compute Tier:** `Basic` (or as required)  
**What to create:**  
- Table `ImageMetadata` with columns:  
  - `Id` (INT, PK, IDENTITY)  
  - `FileName` (NVARCHAR)  
  - `FileSizeKB` (INT)  
  - `Width` (INT)  
  - `Height` (INT)  
  - `Format` (NVARCHAR)  
  - `UploadedOn` (DATETIME2)

---


