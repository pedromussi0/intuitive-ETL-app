# services/scraper/scraper_utils.py

import requests
from bs4 import BeautifulSoup
import zipfile
import os
import logging
from urllib.parse import urljoin
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Define base directory relative to this file's location
# Go up two levels (from services/scraper to intuitivecare_placement_test)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
DEFAULT_ZIP_FILENAME = "Anexos_Rol.zip"

# --- Helper Functions ---

def create_directories():
    """Creates necessary data directories if they don't exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured directories exist: {RAW_DATA_DIR}, {PROCESSED_DATA_DIR}")

def fetch_page(url: str, retries: int = 3, delay: int = 2) -> str | None:
    """Fetches the HTML content of a given URL with retries."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            logging.info(f"Successfully fetched URL: {url}")
            # Explicitly decode using UTF-8, common for Portuguese sites
            # Or let requests guess, but check if content looks garbled
            response.encoding = response.apparent_encoding # Try to guess encoding
            return response.text
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1}/{retries} failed to fetch {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts.")
                return None

def find_pdf_links(html_content: str, base_url: str) -> dict[str, str]:
    """
    Parses HTML to find links to 'Anexo I' and 'Anexo II' PDFs.

    Args:
        html_content: The HTML string of the page.
        base_url: The base URL of the page for resolving relative links.

    Returns:
        A dictionary mapping 'Anexo I' and 'Anexo II' to their absolute URLs.
        Returns empty dict if links are not found.
    """
    soup = BeautifulSoup(html_content, 'lxml') # Using lxml parser
    links = {}
    target_texts = {
        "Anexo I": "Anexo I",  # Key for dict, Text to search (case-insensitive)
        "Anexo II": "Anexo II" # Key for dict, Text to search (case-insensitive)
    }

    # Find all anchor tags potentially containing the PDFs
    # This selector might need adjustment if the site structure changes significantly.
    # We look for links ending in .pdf within the main content area if possible.
    # If not, search all links.
    potential_links = soup.find_all('a', href=lambda href: href and href.lower().endswith('.pdf'))

    if not potential_links:
         potential_links = soup.find_all('a') # Fallback: check all links


    logging.info(f"Found {len(potential_links)} potential PDF links. Searching for targets...")

    found_targets = set()

    for link in potential_links:
        link_text = link.get_text(strip=True)
        href = link.get('href')

        if not href:
            continue

        # Check if this link matches one of our targets
        for target_key, search_text in target_texts.items():
            # Check if we already found this target
            if target_key in found_targets:
                continue

            # Robust check: Case-insensitive check if search_text is in link_text
            # Sometimes the link text might be longer, e.g., "Anexo I - Bla bla bla.pdf"
            # Or sometimes the filename itself in href contains the clue
            if search_text.lower() in link_text.lower() or search_text.replace(" ", "_").lower() in href.lower():
                absolute_url = urljoin(base_url, href)
                logging.info(f"Found potential match for '{target_key}': Text='{link_text}', URL='{absolute_url}'")
                links[target_key] = absolute_url
                found_targets.add(target_key) # Mark as found
                # Optional: Break inner loop if you are certain the first match is the correct one
                # break # Uncomment if first match is desired

        # Stop searching if both targets are found
        if len(found_targets) == len(target_texts):
            break

    if len(links) != len(target_texts):
        logging.warning(f"Could not find all target links. Found: {list(links.keys())}")

    return links


def download_file(url: str, save_path: Path, retries: int = 3, delay: int = 2) -> bool:
    """Downloads a file from a URL and saves it locally with retries."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(retries):
        try:
            # Use stream=True for potentially large files like PDFs
            with requests.get(url, headers=headers, stream=True, timeout=60) as response:
                response.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logging.info(f"Successfully downloaded '{url}' to '{save_path}'")
                return True
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1}/{retries} failed to download {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logging.error(f"Failed to download {url} after {retries} attempts.")
                # Clean up potentially incomplete file
                if save_path.exists():
                    try:
                        os.remove(save_path)
                        logging.info(f"Removed incomplete file: {save_path}")
                    except OSError as rm_err:
                        logging.error(f"Error removing incomplete file {save_path}: {rm_err}")
                return False
    return False # Should not be reached if retries > 0, but good practice

def create_zip(file_paths: list[Path], zip_filename: str) -> bool:
    """
    Creates a ZIP archive containing the specified files.

    Args:
        file_paths: A list of Path objects pointing to the files to be zipped.
        zip_filename: The desired name for the output ZIP file (e.g., Anexos_Rol.zip).

    Returns:
        True if the ZIP file was created successfully, False otherwise.
    """
    zip_filepath = PROCESSED_DATA_DIR / zip_filename
    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                if file_path.exists() and file_path.is_file():
                    # arcname ensures the file is stored with just its name inside the zip
                    zipf.write(file_path, arcname=file_path.name)
                    logging.info(f"Added '{file_path.name}' to '{zip_filepath}'")
                else:
                    logging.warning(f"File not found or is not a file, skipping: {file_path}")
        logging.info(f"Successfully created ZIP archive: '{zip_filepath}'")
        return True
    except zipfile.BadZipFile as e:
        logging.error(f"Failed to create ZIP file '{zip_filepath}': BadZipFile - {e}")
        return False
    except OSError as e:
        logging.error(f"Failed to create ZIP file '{zip_filepath}': OSError - {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during ZIP creation: {e}")
        return False