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
