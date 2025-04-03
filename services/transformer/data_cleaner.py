import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Abbreviation Mapping based on 'Legenda rodapé'
ABBREVIATION_MAP = {
    "OD": "Seg. Odontológica",
    "AMB": "Seg. Ambulatorial",
    "HCO": "Seg. Hospitalar Com Obstetrícia",
    "HSO": "Seg. Hospitalar Sem Obstetrícia",
    "REF": "Plano Referência",
    "PAC": "Procedimento de Alta Complexidade",
    "DUT": "Diretriz de Utilização",
}


def identify_header_and_data(list_of_tables):
    """
    Identifies the header and consolidates data rows from a list of extracted tables.

    Args:
        list_of_tables (list): A list where each item is a table (list of rows).

    Returns:
        tuple: (header, all_data_rows) or (None, []) if header cannot be found
               or data is inconsistent.
    """
    header = None
    all_data_rows = []
    header_found = False

    logging.info("Processing extracted tables to identify header and data...")

    for table_index, table in enumerate(list_of_tables):
        if not table:
            continue  # Skip empty tables

        for row_index, row in enumerate(table):
            # Skip rows that are entirely empty
            if not any(row):
                continue

            # Try to identify header based on common column names
            # Assume it's the first plausible row we encounter across all tables
            if not header_found:
                # Adjust header identification logic if needed
                is_plausible_header = (
                    "PROCEDIMENTO" in row or "OD" in row or "AMB" in row or "RN" in row
                )
                if is_plausible_header:
                    header = row
                    header_found = True
                    logging.info(
                        f"Header identified in table {table_index+1}, row {row_index+1}: {header}"
                    )
                    continue  # Skip the header row itself from data
                else:
                    # Still searching for header, skip this row for now
                    logging.debug(f"Skipping potential non-header row: {row}")
                    continue

            # If header is found, process as data row
            if header is not None:
                # Basic validation: Check if row length matches header length
                if len(row) == len(header):
                    all_data_rows.append(row)
                else:
                    logging.warning(
                        f"Row length mismatch in table {table_index+1}, row {row_index+1}. "
                        f"Header({len(header)}): {header}, Row({len(row)}): {row}. Skipping row."
                    )

    if header is None:
        logging.error("Failed to identify a valid header row in the extracted tables.")
        return None, []

    logging.info(
        f"Header identification complete. Total data rows collected: {len(all_data_rows)}"
    )
    return header, all_data_rows


def transform_data(header, data_rows, mapping=ABBREVIATION_MAP):
    """
    Applies abbreviation transformations to the data rows based on the header.

    Args:
        header (list): The identified header row.
        data_rows (list): List of data rows (lists of strings).
        mapping (dict): Dictionary for abbreviation replacements.

    Returns:
        list: A new list containing the transformed data rows.
    """
    if not header or not data_rows:
        return []

    transformed_data = []
    transform_indices = {}

    # Find column indices for transformation based on the header
    for col_abbr in mapping.keys():
        try:
            transform_indices[col_abbr] = header.index(col_abbr)
        except ValueError:
            logging.warning(
                f"Column '{col_abbr}' for transformation not found in header: {header}"
            )

    if not transform_indices:
        logging.warning(
            "No columns found for transformation based on mapping and header."
        )
        # Return original data if no transformation keys found in header
        return [list(row) for row in data_rows]

    logging.info(
        f"Applying transformations for columns: {list(transform_indices.keys())}"
    )

    for row in data_rows:
        # Important: Create a mutable copy for each row
        transformed_row = list(row)
        for col_abbr, col_index in transform_indices.items():
            try:
                # Check if the cell value exactly matches the abbreviation key
                if transformed_row[col_index] == col_abbr:
                    transformed_row[col_index] = mapping[
                        col_abbr
                    ]  # Perform replacement
            except IndexError:
                # This shouldn't happen if length check passed earlier, but good to handle
                logging.warning(
                    f"IndexError accessing index {col_index} for column '{col_abbr}' in row: {row}. Skipping transformation for this cell."
                )
                continue

        transformed_data.append(transformed_row)

    logging.info(f"Data transformation complete for {len(transformed_data)} rows.")
    return transformed_data
