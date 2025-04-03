import pdfplumber
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def clean_cell_text(text):
    """Cleans extracted cell text by removing newlines and stripping whitespace."""
    if text is None:
        return ""
    return text.replace("\n", " ").strip()


def extract_tables_from_pdf(pdf_path, start_page_num=1):
    """
    Extracts tables from a PDF file starting from a specific page.

    Args:
        pdf_path (str): The path to the input PDF file.
        start_page_num (int): The 1-based page number to start extraction from.

    Returns:
        list: A list of tables, where each table is a list of rows,
              and each row is a list of cleaned cell strings.
              Returns an empty list if the PDF is not found, the start
              page is invalid, or an error occurs.
    """
    extracted_tables_data = []
    page_num_0_based = start_page_num - 1  # Convert to 0-based index

    if not os.path.exists(pdf_path):
        logging.error(f"Input PDF not found at: {pdf_path}")
        return []

    logging.info(f"Opening PDF for table extraction: {pdf_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num_0_based < 0 or page_num_0_based >= len(pdf.pages):
                logging.error(
                    f"Start page ({start_page_num}) is invalid for PDF with {len(pdf.pages)} pages."
                )
                return []

            logging.info(
                f"Starting table extraction from page {start_page_num} (index {page_num_0_based})..."
            )

            for i, page in enumerate(pdf.pages[page_num_0_based:]):
                current_page_num = start_page_num + i
                logging.debug(f"Processing Page {current_page_num}...")

                # Extract tables using default settings (adjust if needed)
                tables_on_page = page.extract_tables()

                if not tables_on_page:
                    logging.debug(f"No tables found on page {current_page_num}.")
                    continue

                # Process each table found on the page
                for table_index, table in enumerate(tables_on_page):
                    if not table:
                        logging.debug(
                            f"Empty table ({table_index+1}) extracted on page {current_page_num}."
                        )
                        continue

                    # Clean the data within the table
                    cleaned_table = []
                    for row_raw in table:
                        cleaned_row = [clean_cell_text(cell) for cell in row_raw]
                        # Optional: Skip rows that are entirely empty after cleaning
                        # if any(cleaned_row):
                        #      cleaned_table.append(cleaned_row)
                        cleaned_table.append(cleaned_row)  # Keep all rows for now

                    if cleaned_table:
                        # Append context if needed (e.g., page number)
                        # For now, just append the list of cleaned rows
                        extracted_tables_data.append(cleaned_table)
                    else:
                        logging.debug(
                            f"Table ({table_index+1}) on page {current_page_num} yielded no data after cleaning."
                        )

    except Exception as e:
        logging.exception(f"An error occurred during PDF table extraction: {e}")
        return []  # Return empty list on error

    logging.info(
        f"PDF table extraction complete. Extracted {len(extracted_tables_data)} table structures."
    )
    return extracted_tables_data
