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
## Code Deployment

> [!NOTE] **BlobTriggerClient**  
> - `__init__.py`: Listens for new blobs in `images-input` and starts the orchestrator with the blob name.  
> - `function.json`: Configures the blob-trigger binding and Durable Functions client output.

> [!NOTE] **OrchestratorFunction**  
> - `__init__.py`: Orchestrates the flow by invoking `ExtractMetadata` then `StoreMetadata`.  
> - `function.json`: Declares the orchestrator trigger and hooks into the Durable Task hub.

> [!NOTE] **ExtractMetadata**  
> - `__init__.py`: Opens the image (via PIL), reads its size, dimensions, and format, then returns a metadata dict.  
> - `function.json`: Defines the activity trigger so the orchestrator can invoke this function.

> [!NOTE] **StoreMetadata**  
> - `__init__.py`: Receives the metadata dict and uses a SQL output binding to insert a row into `ImageMetadata`.  
> - `function.json`: Sets up the activity trigger and the SQL output binding targeting your Azure SQL Database.


### blobtriggerclient
'function.json'
```bash
{
  "bindings": [
    {
      "name": "myblob",
      "type": "blobTrigger",
      "direction": "in",
      "path": "images-input/{name}",
      "connection": "BlobStorageConnectionString"
    },
    {
      "name": "starter",
      "type": "orchestrationClient",              
      "direction": "in"
    }
  ]
}
```
`__init__.py`
```bash
import logging
import azure.functions as func
import azure.durable_functions as df

async def main(
    myblob: func.InputStream,
    starter: df.DurableOrchestrationClient
):
    instance_id = await starter.start_new(
        orchestration_function_name="OrchestratorFunction",
        instance_id=None,
        input=myblob.name
    )
    logging.info(f"✅ Started orchestration for blob '{myblob.name}', instance ID = {instance_id}")

```
### extractmetadata
`function.json`
```bash
{
  "scriptFile": "__init__.py",
  "entryPoint": "main",
  "bindings": [
    {
      "name": "name",
      "type": "activityTrigger",
      "direction": "in"
    }
  ]
}

```
`__init__.py`
```bash
import logging
from PIL import Image
import os

def main(name: str) -> dict:
    # Download blob from the configured storage (the SDK will pick up your connection string)
    from azure.storage.blob import BlobClient
    conn_str = os.getenv("BlobStorageConnectionString")
    blob = BlobClient.from_connection_string(conn_str, container_name="images-input", blob_name=name)
    stream = blob.download_blob().readall()

    img = Image.open(io.BytesIO(stream))
    metadata = {
        "file_name": name,
        "file_size_kb": len(stream) // 1024,
        "width": img.width,
        "height": img.height,
        "format": img.format
    }
    logging.info(f"🖼 Extracted metadata for {name}: {metadata}")
    return metadata

```
### orchestratorfunction
`function.json`
```bash
{
  "scriptFile": "__init__.py",
  "entryPoint": "main",
  "bindings": [
    {
      "name": "context",
      "type": "durableOrchestrationTrigger",
      "direction": "in"
    }
  ]
}

```
`__init__.py`
```bash
import azure.durable_functions as df

def main(context: df.DurableOrchestrationContext):
    image_name = context.get_input()
    metadata   = yield context.call_activity("ExtractMetadata", image_name)
    yield       context.call_activity("StoreMetadata", metadata)
    return      metadata

```
### storemetadata

`function.json`
```bash
{
  "scriptFile": "__init__.py",
  "entryPoint": "main",
  "bindings": [
    {
      "name": "metadata",
      "type": "activityTrigger",
      "direction": "in"
    },
    {
      "name": "row",
      "type": "sql",
      "direction": "out",
      "commandText": "INSERT INTO ImageMetadata (FileName, FileSizeKB, Width, Height, Format) VALUES (@file_name, @file_size_kb, @width, @height, @format)",
      "connectionStringSetting": "SqlConnectionString"
    }
  ]
}

```
`__init__.py`

```bash
import logging
import azure.functions as func

def main(metadata: dict, row: func.Out[func.SqlRow]) -> None:
    sql_row = func.SqlRow.from_dict({
        "file_name": metadata["file_name"],
        "file_size_kb": metadata["file_size_kb"],
        "width": metadata["width"],
        "height": metadata["height"],
        "format": metadata["format"]
    })
    row.set(sql_row)
    logging.info(f"💾 Queued SQL insert for '{metadata['file_name']}'")

```
## Section 3: Deployment & Testing

### 3.1 Publish to Azure  
```bash
# 1. Log in and select your subscription
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"

# 2. From your function app root folder, publish all functions
func azure functionapp publish imagemetadatafuncapp --python

### Testing the Image Metadata Pipeline

1. **Upload an Image**  
   - Add a `.jpg`, `.png`, or `.gif` file to the `images-input` container via Azure Portal or Storage Explorer.

2. **Watch the Log Stream**  
   - In Azure Portal, navigate to your Function App → **Monitoring** → **Log stream**.  
   - Confirm you see:
     - `Started orchestration for blob: <your‑file>`
     - Calls to `ExtractMetadata` and `StoreMetadata`.

3. **Query the SQL Table**  
   - In Azure Portal, go to **SQL databases** → `imagemetadata-db` → **Query editor**.  
   - Run:
     ```sql
     SELECT TOP 5 * 
       FROM ImageMetadata 
     ORDER BY UploadedOn DESC;
     ```
   - Verify a new row with your file’s name, size, dimensions, and format.

