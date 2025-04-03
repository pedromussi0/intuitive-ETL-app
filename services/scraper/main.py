# services/scraper/main.py

import logging
from pathlib import Path
import sys

# Ensure the parent directory (services) is in the Python path
# to allow imports from scraper_utils
# This might be needed depending on how you run the script
# current_dir = Path(__file__).resolve().parent
# service_dir = current_dir.parent
# project_dir = service_dir.parent
# sys.path.insert(0, str(project_dir))
# print(f"Adjusted sys.path: {sys.path}") # Debug print

# Use relative import if running as part of a package structure
try:
    from .scraper_utils import (
        fetch_page,
        find_pdf_links,
        download_file,
        create_zip,
        create_directories,
        RAW_DATA_DIR,
        DEFAULT_ZIP_FILENAME,
    )
except ImportError:
    # Fallback for running script directly
    from scraper_utils import (
        fetch_page,
        find_pdf_links,
        download_file,
        create_zip,
        create_directories,
        RAW_DATA_DIR,
        DEFAULT_ZIP_FILENAME,
    )


# --- Configuration ---
TARGET_URL = "https://www.gov.br/ans/pt-br/acesso-a-informacao/participacao-da-sociedade/atualizacao-do-rol-de-procedimentos"

# --- Main Execution Logic ---


def run_scraper():
    """Main function to orchestrate the scraping process."""
    logging.info("--- Starting Scraper ---")

    # 0. Ensure directories exist
    create_directories()

    # 1. Fetch the main page
    logging.info(f"Fetching main page: {TARGET_URL}")
    html_content = fetch_page(TARGET_URL)
    if not html_content:
        logging.error("Aborting script: Could not fetch the main page.")
        return False

    # 2. Find the PDF links
    logging.info("Parsing page to find Anexo I and Anexo II PDF links...")
    pdf_links = find_pdf_links(html_content, TARGET_URL)

    if not pdf_links or len(pdf_links) < 2:
        logging.error(
            f"Aborting script: Could not find links for both Anexo I and Anexo II. Found: {pdf_links}"
        )
        return False  # Exit if we didn't find both required links

    logging.info(f"Found PDF links: {pdf_links}")

    # 3. Download the PDFs
    downloaded_files = []
    download_successful = True
    for name, url in pdf_links.items():
        # Sanitize filename slightly (replace space with underscore)
        filename = f"{name.replace(' ', '_').lower()}.pdf"
        save_path = RAW_DATA_DIR / filename
        logging.info(f"Attempting to download {name} from {url} to {save_path}")
        if download_file(url, save_path):
            downloaded_files.append(save_path)
        else:
            logging.error(f"Failed to download {name}. Aborting zip creation.")
            download_successful = False

    if not download_successful or len(downloaded_files) != len(pdf_links):
        logging.error(
            "Aborting script: Not all required PDFs were downloaded successfully."
        )
        return False

    # 4. Create the ZIP archive
    logging.info("Creating ZIP archive...")
    zip_created = create_zip(downloaded_files, DEFAULT_ZIP_FILENAME)

    if zip_created:
        logging.info("--- Scraper finished successfully ---")
        return True
    else:
        logging.error("--- Scraper finished with errors (ZIP creation failed) ---")
        return False


if __name__ == "__main__":
    run_scraper()
