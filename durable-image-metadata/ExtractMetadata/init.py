import os, logging
from PIL import Image

def main(name: str) -> dict:
    # Adjust base path if needed
    base = os.getenv("AzureWebJobsScriptRoot", ".")
    path = os.path.join(base, "images-input", name)

    with Image.open(path) as img:
        metadata = {
          "file_name":   name,
          "file_size_kb": os.path.getsize(path) // 1024,
          "width":        img.width,
          "height":       img.height,
          "format":       img.format
        }
    logging.info(f"🛠️ Extracted metadata for '{name}': {metadata}")
    return metadata
