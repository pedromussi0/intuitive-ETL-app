import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re
import zipfile
import io

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Configuration ---
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))
)  # Navigate up to project root
DOWNLOAD_DIR = os.path.join(BASE_DIR, "data", "raw", "db_source")

ACCOUNTING_DATA_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
OPERATORS_DATA_URL = (
    "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
)


TARGET_YEARS = [2023, 2024]
# --- End Configuration ---


def download_file(url, target_path):
    """Downloads a file from a URL to a target path."""
    try:
        # Add headers to mimic a browser request, sometimes helps
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(
            url, stream=True, headers=headers, timeout=60
        )  # Added headers and timeout
        response.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Successfully downloaded: {os.path.basename(target_path)}")
        return True
    except requests.exceptions.Timeout:
        logging.error(f"Timeout error while downloading {url}")
        return False
    except requests.exceptions.HTTPError as http_err:
        logging.error(
            f"HTTP error occurred while downloading {url}: {http_err} - Status Code: {http_err.response.status_code}"
        )
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        logging.error(f"An error occurred saving {target_path}: {e}")
        return False


def unzip_file(zip_path, extract_to_dir):
    """Unzips a file to a specified directory."""
    extracted_files = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to_dir)
            extracted_files = zip_ref.namelist()
        logging.info(
            f"Successfully unzipped: {os.path.basename(zip_path)} to {extract_to_dir}. Extracted: {extracted_files}"
        )

        return True
    except zipfile.BadZipFile:
        logging.error(f"Error: {zip_path} is not a zip file or is corrupted.")
        return False
    except Exception as e:
        logging.error(f"Failed to unzip {zip_path}: {e}")
        return False


def download_accounting_data(base_url, target_dir, years_to_download):
    """Downloads and unzips quarterly accounting data for specified years."""
    logging.info(f"Starting download of accounting data for years: {years_to_download}")
    downloaded_count = 0

    for year in years_to_download:
        year_url = urljoin(base_url, f"{year}/")
        logging.info(f"Accessing directory for year {year}: {year_url}")

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            dir_response = requests.get(year_url, headers=headers, timeout=30)
            dir_response.raise_for_status()  # Check for 4xx/5xx errors
            dir_soup = BeautifulSoup(dir_response.text, "html.parser")

            zip_links = []
            # Find all 'a' tags and filter for .zip files
            for link in dir_soup.find_all("a"):
                href = link.get("href")
                # Ensure href exists and ends with .zip (case-insensitive)
                if href and href.lower().endswith(".zip"):
                    # Make sure it's not a link to parent dir or similar
                    if not href.startswith("?") and href != "../":
                        zip_links.append(
                            urljoin(year_url, href)
                        )  # Construct absolute URL

            if not zip_links:
                logging.warning(f"No .zip files found in directory for year {year}.")
                continue  # Move to the next year

            logging.info(f"Found {len(zip_links)} zip file(s) for year {year}.")
            year_downloaded_successfully = False
            for zip_url in zip_links:
                zip_filename = os.path.basename(zip_url)
                zip_path = os.path.join(target_dir, zip_filename)

                logging.info(f"Attempting to download {zip_filename}...")
                if download_file(zip_url, zip_path):
                    if unzip_file(zip_path, target_dir):
                        year_downloaded_successfully = (
                            True  # Mark success if at least one file is processed
                        )
                    else:
                        logging.warning(
                            f"Could not unzip {zip_filename}. Please check the file manually."
                        )
                else:
                    logging.warning(f"Failed to download {zip_filename}.")

            if year_downloaded_successfully:
                downloaded_count += (
                    1  # Increment count if any file from the year was processed
                )

        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 404:
                logging.warning(
                    f"Directory for year {year} not found (404): {year_url}"
                )
            else:
                logging.error(f"HTTP error accessing directory {year_url}: {http_err}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to access or process directory {year_url}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred processing year {year}: {e}")

    logging.info(
        f"Finished accounting data download attempt. Processed data for {downloaded_count} year(s)."
    )


def download_operator_data(base_url, target_dir):
    """Downloads the active operators CSV file."""
    logging.info(f"Starting download of operator data from {base_url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        csv_link = None
        links = soup.find_all("a")
        # Look for specific filename if known, otherwise first csv
        # Example: Find 'Relatorio_cadop.csv' specifically
        known_filename = "Relatorio_cadop.csv"  
        found = False
        for link in links:
            href = link.get("href")
            if href and os.path.basename(href).lower() == known_filename.lower():
                csv_link = urljoin(base_url, href)
                found = True
                break

        # Fallback: if specific name not found, take the first .csv
        if not found:
            for link in links:
                href = link.get("href")
                if href and href.lower().endswith(".csv"):
                    csv_link = urljoin(base_url, href)
                    logging.info(
                        f"Specific operator file '{known_filename}' not found, using first CSV found: {os.path.basename(csv_link)}"
                    )
                    break

        if csv_link:
            file_name = os.path.basename(csv_link)
            file_path = os.path.join(target_dir, file_name)
            download_file(csv_link, file_path)
        else:
            logging.warning(f"Could not find any CSV download link at {base_url}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to access operator data URL {base_url}: {e}")
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during operator data download: {e}"
        )


if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    logging.info(f"Ensured download directory exists: {DOWNLOAD_DIR}")

    # Task 3.1: Download Accounting Data (Specific Years: 2023, 2024)
    # Pass the list of target years directly
    download_accounting_data(ACCOUNTING_DATA_URL, DOWNLOAD_DIR, TARGET_YEARS)

    # Task 3.2: Download Operator Data
    download_operator_data(OPERATORS_DATA_URL, DOWNLOAD_DIR)

    logging.info("Download process finished.")
