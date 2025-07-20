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
