import os
import csv
import zipfile
import logging

from pdf_parser import extract_tables_from_pdf
from data_cleaner import identify_header_and_data, transform_data

# --- Configuration ---
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)  # Project Root
INPUT_PDF_PATH = os.path.join(BASE_DIR, "data", "raw", "anexo_i.pdf")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_CSV_FILENAME = "rol_procedimentos.csv"

MEU_NOME = "pedro_mussi"
OUTPUT_ZIP_FILENAME = f"Teste_{MEU_NOME}.zip"
START_PAGE = 3  # Page number where data extraction begins (1-based index)

# Logging Setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# --- End Configuration ---


def save_to_csv(header, data, csv_filepath):
    """Saves the header and data rows to a CSV file."""
    try:
        logging.info(f"Saving data to CSV: {csv_filepath}")
        os.makedirs(os.path.dirname(csv_filepath), exist_ok=True)
        with open(csv_filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow(header)
            writer.writerows(data)
        logging.info(f"Successfully saved {len(data)} rows to {csv_filepath}")
        return True
    except Exception as e:
        logging.exception(f"Failed to save data to CSV: {e}")
        return False


def compress_to_zip(file_to_compress, zip_filepath):
    """Compresses a single file into a ZIP archive."""
    try:
        logging.info(
            f"Compressing {os.path.basename(file_to_compress)} to {zip_filepath}"
        )
        os.makedirs(os.path.dirname(zip_filepath), exist_ok=True)
        with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(file_to_compress, arcname=os.path.basename(file_to_compress))
        logging.info(f"Successfully created ZIP archive: {zip_filepath}")
        return True
    except Exception as e:
        logging.exception(f"Failed to create ZIP archive: {e}")
        return False


# --- Main Execution ---
if __name__ == "__main__":
    logging.info("Starting PDF Transformation Process...")
    success = False
    csv_file_path = os.path.join(OUTPUT_DIR, OUTPUT_CSV_FILENAME)
    zip_file_path = os.path.join(OUTPUT_DIR, OUTPUT_ZIP_FILENAME)

    # Step 1: Extract raw table data from PDF
    raw_tables = extract_tables_from_pdf(
        pdf_path=INPUT_PDF_PATH, start_page_num=START_PAGE
    )

    if raw_tables:
        # Step 2: Identify header and consolidate data rows
        header, consolidated_data = identify_header_and_data(raw_tables)

        if header and consolidated_data:
            # Step 3: Transform the data (apply mappings)
            transformed_data = transform_data(
                header, consolidated_data
            )  # Uses default mapping

            # Step 4: Save transformed data to CSV
            if save_to_csv(header, transformed_data, csv_file_path):
                # Step 5: Compress the CSV to ZIP
                success = compress_to_zip(csv_file_path, zip_file_path)
            else:
                logging.error("CSV saving failed, skipping compression.")
        else:
            logging.error("Header identification or data consolidation failed.")
    else:
        logging.error("PDF table extraction failed or yielded no tables.")

    if success:
        logging.info("Process completed successfully.")
        # Optional: Remove the intermediate CSV file after zipping
        # try: os.remove(csv_file_path)
        # except OSError as e: logging.warning(f"Could not remove intermediate CSV: {e}")
    else:
        logging.error("Process finished with errors.")
