import os
import csv
import glob
import psycopg2
from psycopg2.extras import execute_batch
from decimal import Decimal, InvalidOperation
from datetime import datetime
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Load Environment Variables ---
# Load variables from .env file in the project root
dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
)
load_dotenv(dotenv_path=dotenv_path)

# --- Database Configuration from Environment ---
DB_NAME = os.getenv("POSTGRES_DB", "ans_data")
DB_USER = os.getenv("POSTGRES_USER", "ans_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "db")

try:
    DB_PORT = os.getenv("DB_PORT_HOST")
except ValueError:
    logging.warning("DB_PORT_HOST is not a valid integer, defaulting to 5432")
    DB_PORT = 5432


# --- File Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw", "db_source")
OPERATOR_FILE_PATTERN = "Relatorio_cadop*.csv"
ACCOUNTING_FILE_PATTERN = "*T*.csv"  
FILE_ENCODING = "utf-8"
DELIMITER = ";"
# ---


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = None
    try:
        if not DB_PASSWORD:
            raise ValueError("DB_PASSWORD environment variable not set.")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        logging.info(f"Database connection successful to {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Database connection failed: {e}")
        logging.error(
            f"Check connection parameters: Host={DB_HOST}, Port={DB_PORT}, DB={DB_NAME}, User={DB_USER}"
        )
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred during DB connection: {e}")
        raise


def parse_date(date_str, formats=["%Y-%m-%d", "%d/%m/%Y"]):
    """Tries multiple formats to parse a date string."""
    if not date_str:
        return None
    for fmt in formats:
        try:
            # Handle potential extra whitespace
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    logging.warning(f"Could not parse date: '{date_str}' with formats {formats}")
    return None


def parse_decimal(decimal_str):
    """Safely parses a string to a Decimal, handling pt-BR format."""
    if not decimal_str:
        return None
    try:
        # Handle potential thousands separators ('.') and decimal comma (',')
        cleaned_str = decimal_str.strip().replace(".", "").replace(",", ".")
        # Handle potential negative signs represented by parentheses
        if cleaned_str.startswith("(") and cleaned_str.endswith(")"):
            cleaned_str = "-" + cleaned_str[1:-1]
        return Decimal(cleaned_str)
    except InvalidOperation:
        logging.warning(f"Could not parse decimal: '{decimal_str}'")
        return None


def import_operadoras(conn, file_path):
    """Imports operadoras data, truncating the table first."""
    logging.info(f"Importing operadoras from: {file_path}")
    inserted_count = 0
    skipped_count = 0
    cursor = None
    try:
        cursor = conn.cursor()

        # --- Truncate table before import ---
        logging.warning("Truncating operadoras table (CASCADE)...")
        cursor.execute("TRUNCATE TABLE operadoras CASCADE;")
        logging.info("Operadoras table truncated.")
        # ---

        with open(file_path, mode="r", encoding=FILE_ENCODING) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=DELIMITER)
            sql_columns = [
                "Registro_ANS",
                "CNPJ",
                "Razao_Social",
                "Nome_Fantasia",
                "Modalidade",
                "Logradouro",
                "Numero",
                "Complemento",
                "Bairro",
                "Cidade",
                "UF",
                "CEP",
                "DDD",
                "Telefone",
                "Fax",
                "Endereco_eletronico",
                "Representante",
                "Cargo_Representante",
                "Data_Registro_ANS",
            ]
            placeholders = ", ".join(["%s"] * len(sql_columns))
            sql = f"""
                INSERT INTO operadoras ({', '.join(sql_columns)})
                VALUES ({placeholders})
                ON CONFLICT (Registro_ANS) DO NOTHING;
            """

            for row_num, row in enumerate(reader, 1):
                try:
                    # Prepare data tuple in the correct order for sql_columns
                    data_tuple = []
                    # Clean and prepare data - use .get() with defaults for safety
                    reg_ans_str = row.get(
                        "Registro ANS"
                    )  # Handle potential space in header
                    if reg_ans_str is None:
                        reg_ans_str = row.get("Registro_ANS")  # Fallback

                    reg_ans = (
                        int(reg_ans_str)
                        if reg_ans_str and reg_ans_str.isdigit()
                        else None
                    )
                    data_reg_ans = parse_date(row.get("Data_Registro_ANS"))

                    if reg_ans is None:
                        logging.warning(
                            f"Skipping row {row_num} due to missing or invalid Registro_ANS: {row}"
                        )
                        skipped_count += 1
                        continue

                    data_tuple = (
                        reg_ans,
                        row.get("CNPJ"),
                        row.get("Razao_Social"),
                        row.get("Nome_Fantasia"),
                        row.get("Modalidade"),
                        row.get("Logradouro"),
                        row.get("Numero"),
                        row.get("Complemento"),
                        row.get("Bairro"),
                        row.get("Cidade"),
                        row.get("UF"),
                        row.get("CEP"),
                        row.get("DDD"),
                        row.get("Telefone"),
                        row.get("Fax"),
                        row.get("Endereco_eletronico"),
                        row.get("Representante"),
                        row.get("Cargo_Representante"),
                        data_reg_ans,
                    )

                    if len(data_tuple) != len(sql_columns):
                        raise ValueError(
                            f"Row {row_num}: Mismatch between data tuple size ({len(data_tuple)}) and expected columns ({len(sql_columns)})"
                        )

                    cursor.execute(sql, data_tuple)
                    inserted_count += 1
                except (ValueError, TypeError, KeyError) as data_error:
                    logging.error(
                        f"Error processing row {row_num}: {row} - {data_error}"
                    )
                    skipped_count += 1

                except Exception as row_error:
                    logging.error(
                        f"Unexpected error processing row {row_num}: {row} - {row_error}"
                    )
                    skipped_count += 1

            conn.commit()
            logging.info(
                f"Finished importing operadoras. Inserted: {inserted_count}, Skipped: {skipped_count}"
            )

    except FileNotFoundError:
        logging.error(f"Operator file not found: {file_path}")
    except Exception as e:
        logging.error(f"Error importing operadoras: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()


def import_demonstracoes_batch(
    conn, file_path, valid_ans_set, batch_size=1000
):  # Added valid_ans_set parameter
    """
    Imports demonstracoes contabeis data, skipping rows where REG_ANS
    is not found in the provided valid_ans_set. Includes VL_SALDO_INICIAL.
    """
    global FILE_ENCODING, DELIMITER, parse_date, parse_decimal

    base_filename = os.path.basename(file_path)
    logging.info(
        f"Importing demonstracoes from: {base_filename}, checking against {len(valid_ans_set)} valid ANS."
    )
    inserted_count = 0
    skipped_invalid_ans = 0
    skipped_other = 0
    batch = []
    cursor = None
    file_succeeded = True

    try:
        cursor = conn.cursor()
        with open(file_path, mode="r", encoding=FILE_ENCODING) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=DELIMITER)

            sql = """
                INSERT INTO demonstracoes_contabeis (
                    DATA, REGISTRO_ANS, CONTA_CONTABIL, DESCRICAO,
                    VL_SALDO_INICIAL, VL_SALDO_FINAL
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                );
            """

            for row_num, row in enumerate(reader, 1):
                # --- Process Row Data ---
                try:
                    reg_ans_str = row.get("REG_ANS")
                    reg_ans = (
                        int(reg_ans_str)
                        if reg_ans_str and reg_ans_str.isdigit()
                        else None
                    )

                    if reg_ans not in valid_ans_set:
                        if skipped_invalid_ans % 1000 == 0:  # Log every 1000 skips
                            logging.debug(
                                f"Skipping row {row_num} in {base_filename}: REG_ANS {reg_ans} not in valid set. (Sample log)"
                            )
                        skipped_invalid_ans += 1
                        continue

                    # --- If REG_ANS is valid, proceed with parsing other fields ---
                    data_dt = parse_date(row.get("DATA"))
                    conta_contabil = row.get("CD_CONTA_CONTABIL")
                    descricao = row.get("DESCRICAO")
                    vl_saldo_inicial = parse_decimal(row.get("VL_SALDO_INICIAL"))
                    vl_saldo_final = parse_decimal(row.get("VL_SALDO_FINAL"))

                    # Check other required fields (excluding reg_ans as it's already validated)
                    if data_dt is None or conta_contabil is None or descricao is None:
                        logging.warning(
                            f"Skipping row {row_num} in {base_filename} due to missing required fields (DATA, CD_CONTA_CONTABIL, or DESCRICAO): {row}"
                        )
                        skipped_other += 1
                        continue

                    # Prepare tuple if all checks pass
                    data_tuple = (
                        data_dt,
                        reg_ans,
                        conta_contabil,
                        descricao,
                        vl_saldo_inicial,
                        vl_saldo_final,
                    )
                    batch.append(data_tuple)

                except (ValueError, TypeError, KeyError) as data_error:
                    logging.error(
                        f"Data processing error on row {row_num} in {base_filename} (REG_ANS: {reg_ans}): {row} - Error: {data_error}"
                    )
                    skipped_other += 1
                    continue  # Skip this row
                except Exception as proc_error:
                    logging.error(
                        f"Unexpected row processing error on row {row_num} in {base_filename} (REG_ANS: {reg_ans}): {row} - Error: {proc_error}"
                    )
                    skipped_other += 1
                    continue  # Skip this row

                # --- Execute Batch when Full ---
                if len(batch) >= batch_size:
                    try:
                        execute_batch(cursor, sql, batch)
                        conn.commit()
                        inserted_count += len(batch)
                        logging.debug(
                            f"Committed batch of {len(batch)} rows for {base_filename}"
                        )
                        batch = []
                    except (psycopg2.DatabaseError, psycopg2.InterfaceError) as db_err:
                        logging.error(
                            f"Database error during batch insert for {base_filename} (near row {row_num}): {db_err}"
                        )

                        conn.rollback()
                        logging.warning(
                            f"Transaction rolled back for {base_filename} due to batch error."
                        )
                        file_succeeded = False
                        break  # Exit loop for this file
                    except Exception as batch_exec_err:
                        logging.error(
                            f"Unexpected error during batch execution for {base_filename} (near row {row_num}): {batch_exec_err}"
                        )
                        conn.rollback()
                        logging.warning(
                            f"Transaction rolled back for {base_filename} due to unexpected batch error."
                        )
                        file_succeeded = False
                        break

            # --- Process Final Batch ---
            if file_succeeded and batch:
                try:
                    execute_batch(cursor, sql, batch)
                    conn.commit()
                    inserted_count += len(batch)
                    logging.debug(
                        f"Committed final batch of {len(batch)} rows for {base_filename}"
                    )
                except (psycopg2.DatabaseError, psycopg2.InterfaceError) as db_err:
                    logging.error(
                        f"Database error during final batch insert for {base_filename}: {db_err}"
                    )
                    conn.rollback()
                    logging.warning(
                        f"Transaction rolled back for final batch of {base_filename}."
                    )
                    file_succeeded = False
                except Exception as final_batch_err:
                    logging.error(
                        f"Unexpected error during final batch execution for {base_filename}: {final_batch_err}"
                    )
                    conn.rollback()
                    logging.warning(
                        f"Transaction rolled back for final batch of {base_filename} due to unexpected error."
                    )
                    file_succeeded = False

        # Log final status for the file including skip counts
        total_skipped = skipped_invalid_ans + skipped_other
        log_level = logging.INFO if file_succeeded else logging.ERROR
        logging.log(
            log_level,
            f"Finished processing {base_filename}. Success: {file_succeeded}. "
            f"Inserted: {inserted_count}, Skipped (Invalid ANS): {skipped_invalid_ans}, "
            f"Skipped (Other): {skipped_other}, Total Skipped: {total_skipped}",
        )

        return file_succeeded

    except FileNotFoundError:
        logging.error(f"Accounting file not found: {file_path}")
        return False
    except Exception as e:
        logging.error(f"General error processing file {base_filename}: {e}")
        if conn and not conn.autocommit:
            try:
                conn.rollback()
            except Exception:
                pass
        return False
    finally:
        if cursor:
            cursor.close()


if __name__ == "__main__":
    connection = None
    valid_ans_set = set()
    try:
        connection = get_db_connection()
        connection.autocommit = False  # Ensure transactions are managed explicitly

        # --- Import Operadoras (Truncates inside function) ---
        operator_files = glob.glob(os.path.join(DATA_DIR, OPERATOR_FILE_PATTERN))
        if operator_files:
            import_operadoras(connection, operator_files[0])
        else:
            logging.warning(
                f"No operator file matching '{OPERATOR_FILE_PATTERN}' found in {DATA_DIR}"
            )

        # --- Pre-fetch valid REGISTRO_ANS values AFTER operators are imported ---
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT "registro_ans" FROM operadoras')
            # Fetch all results and add the first element of each row (the ID) to the set
            valid_ans_set = {row[0] for row in cursor.fetchall()}
            cursor.close()
            logging.info(
                f"Loaded {len(valid_ans_set)} valid REG_ANS values from operadoras table into memory."
            )
            if not valid_ans_set:
                logging.warning(
                    "No valid REG_ANS values found in operadoras table. Accounting import might skip all rows."
                )
        except Exception as fetch_err:
            logging.error(
                f"Failed to fetch REG_ANS values from operadoras table: {fetch_err}"
            )

            raise SystemExit("Cannot proceed without valid ANS list.")

        # --- Import Demonstracoes Contabeis ---
        accounting_files = glob.glob(os.path.join(DATA_DIR, ACCOUNTING_FILE_PATTERN))
        if accounting_files:
            logging.info(f"Found {len(accounting_files)} accounting files to import.")

            # --- Truncate demonstracoes_contabeis table before importing ANY accounting files ---
            cursor = connection.cursor()
            try:
                logging.warning("Truncating demonstracoes_contabeis table...")
                cursor.execute("TRUNCATE TABLE demonstracoes_contabeis;")
                connection.commit()  # Commit the truncate before starting file imports
                logging.info("Demonstracoes_contabeis table truncated.")
            except Exception as trunc_error:
                logging.error(
                    f"Failed to truncate demonstracoes_contabeis: {trunc_error}"
                )
                connection.rollback()  # Rollback if truncate fails
                raise  # Stop the import if we can't truncate
            finally:
                if cursor:
                    cursor.close()
            # ---

            # Import files one by one
            successful_files = 0
            failed_files = 0
            for acc_file in sorted(
                accounting_files
            ):  # Sort ensures some order if needed
                if import_demonstracoes_batch(
                    connection, acc_file, valid_ans_set=valid_ans_set
                ):  # Use batch import
                    successful_files += 1
                else:
                    failed_files += 1
            logging.info(
                f"Accounting file import summary: Successful={successful_files}, Failed={failed_files}"
            )

        else:
            logging.warning(
                f"No accounting files matching '{ACCOUNTING_FILE_PATTERN}' found in {DATA_DIR}"
            )

        logging.info("Import process finished.")

    except Exception as e:
        logging.error(f"An critical error occurred during the import process: {e}")
    finally:
        if connection:
            connection.close()
            logging.info("Database connection closed.")
