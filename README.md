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

1. **Create resource group**:
   ```bash
   az group create -n image-processor-rg -l eastus
   ```
2. **Create storage account**:
   ```bash
   az storage account create \
     -n mystorageacct123 \
     -g image-processor-rg \
     -l eastus \
     --sku Standard_LRS
   ```
3. **Create blob containers**:
   ```bash
   az storage container create -n images-input --account-name mystorageacct123
   ```
4. **Deploy Function App**:
   ```bash
   az functionapp create \
     -g image-processor-rg \
     -n image-processor-func \
     --storage-account mystorageacct123 \
     --runtime python \
     --functions-version 4
   ```
5. **Configure application settings**:
   ```bash
   az functionapp config appsettings set \
     -n image-processor-func -g image-processor-rg \
     --settings \
       AzureWebJobsStorage="<connection-string>" \
       FUNCTIONS_EXTENSION_VERSION="~4" \
       FUNCTIONS_WORKER_RUNTIME="python" \
       APPINSIGHTS_INSTRUMENTATIONKEY="<ikey>"
   ```

### Configuration

- Update `local.settings.json` (for local dev) with:
  ```json
  {
    "IsEncrypted": false,
    "Values": {
      "AzureWebJobsStorage": "<conn>",
      "FUNCTIONS_WORKER_RUNTIME": "python",
      "BlobStorageConnectionString": "<conn>"
    }
  }
  ```

### Deploying Functions

```bash
func azure functionapp publish image-processor-func
```

---

## Local Development

1. Clone the repo.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Functions host locally:
   ```bash
   func start
   ```
4. Upload sample images to `images-input` container or place them in `local.settings.json`-backed blob emulator.

---
