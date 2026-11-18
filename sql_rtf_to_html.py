"""
SQL Server RTF to HTML Converter

Decompresses SQL Server compressed RTF data, converts it to HTML using
the external RTF2HTML executable, and updates the corresponding database
records.

Configuration is loaded from environment variables or a .env file.
"""

import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pyodbc
from compressed_rtf import decompress
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()


def get_config(name, default=None):
    """Read a configuration value from environment variables."""
    value = os.getenv(name, default)

    if value is None or not value.strip():
        raise ValueError(f"Missing required configuration: {name}")

    return value.strip()


DB_DRIVER = get_config("DB_DRIVER", "ODBC Driver 18 for SQL Server")
DB_SERVER = get_config("DB_SERVER")
DB_NAME = get_config("DB_NAME")

DB_TRUSTED_CONNECTION = (
    get_config("DB_TRUSTED_CONNECTION", "yes").lower() == "yes"
)

DB_USERNAME = os.getenv("DB_USERNAME", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DB_TRUST_SERVER_CERTIFICATE = (
    get_config("DB_TRUST_SERVER_CERTIFICATE", "yes").lower() == "yes"
)

DB_TABLE = get_config("DB_TABLE")
DB_ID_COLUMN = get_config("DB_ID_COLUMN")
DB_SOURCE_COLUMN = get_config("DB_SOURCE_COLUMN")
DB_HTML_COLUMN = get_config("DB_HTML_COLUMN")

RTF2HTML_EXE = Path(get_config("RTF2HTML_EXE"))

BATCH_SIZE = int(get_config("BATCH_SIZE", "50"))
LOG_FILE = get_config("LOG_FILE", "rtf_conversion.log")


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# SQL IDENTIFIER VALIDATION
# ============================================================

def quote_identifier(identifier):
    """
    Validate and quote SQL Server identifiers.

    Supports schema.table notation for table names.
    Does not accept arbitrary SQL expressions.
    """

    parts = identifier.split(".")

    for part in parts:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part):
            raise ValueError(
                f"Invalid SQL identifier: {identifier}"
            )

    return ".".join(f"[{part}]" for part in parts)


TABLE = quote_identifier(DB_TABLE)
ID_COLUMN = quote_identifier(DB_ID_COLUMN)
SOURCE_COLUMN = quote_identifier(DB_SOURCE_COLUMN)
HTML_COLUMN = quote_identifier(DB_HTML_COLUMN)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def create_connection():
    """Create a connection to SQL Server."""

    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"TrustServerCertificate={'yes' if DB_TRUST_SERVER_CERTIFICATE else 'no'};"
    )

    if DB_TRUSTED_CONNECTION:
        connection_string += "Trusted_Connection=yes;"
    else:
        connection_string += (
            f"UID={DB_USERNAME};"
            f"PWD={DB_PASSWORD};"
        )

    return pyodbc.connect(connection_string)


# ============================================================
# RTF DECOMPRESSION
# ============================================================

def decompress_rtf(compressed_data):
    """Decompress SQL Server compressed RTF data."""

    if isinstance(compressed_data, memoryview):
        compressed_data = compressed_data.tobytes()

    if not isinstance(compressed_data, bytes):
        compressed_data = bytes(compressed_data)

    return decompress(compressed_data)


# ============================================================
# RTF TO HTML CONVERSION
# ============================================================

def convert_rtf_to_html(rtf_data):
    """
    Convert decompressed RTF data into HTML using RTF2HTML.

    Temporary files are automatically removed after conversion.
    """

    if not RTF2HTML_EXE.is_file():
        raise FileNotFoundError(
            f"RTF2HTML executable not found: {RTF2HTML_EXE}"
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        rtf_file = temp_path / "input.rtf"
        html_file = temp_path / "output.html"

        # Write decompressed RTF data to a temporary file.
        if isinstance(rtf_data, str):
            rtf_data = rtf_data.encode("utf-8")

        rtf_file.write_bytes(rtf_data)

        # Execute the external RTF2HTML converter.
        result = subprocess.run(
            [
                str(RTF2HTML_EXE),
                str(rtf_file),
                str(html_file)
            ],
            capture_output=True,
            text=True,
            check=True
        )

        if result.stderr:
            logger.warning("RTF2HTML output: %s", result.stderr.strip())

        if not html_file.exists():
            raise FileNotFoundError(
                "RTF2HTML did not generate the expected HTML file."
            )

        html_data = html_file.read_bytes()

        # Decode the generated HTML.
        try:
            return html_data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return html_data.decode("cp1252", errors="replace")


# ============================================================
# MAIN PROCESSING
# ============================================================

def main():

    logger.info("Starting SQL Server RTF to HTML conversion.")

    connection = None

    try:
        connection = create_connection()
        cursor = connection.cursor()

        # Retrieve records that contain compressed RTF data
        # but do not yet have converted HTML content.
        select_query = f"""
            SELECT
                {ID_COLUMN},
                {SOURCE_COLUMN}
            FROM {TABLE}
            WHERE
                {SOURCE_COLUMN} IS NOT NULL
                AND {HTML_COLUMN} IS NULL
        """

        cursor.execute(select_query)
        records = cursor.fetchall()

        total_records = len(records)

        logger.info("Records found: %s", total_records)

        if total_records == 0:
            logger.info("No records require conversion.")
            return

        update_query = f"""
            UPDATE {TABLE}
            SET {HTML_COLUMN} = ?
            WHERE {ID_COLUMN} = ?
        """

        successful = 0
        failed = 0

        for index, record in enumerate(records, start=1):

            record_id = record[0]
            compressed_data = record[1]

            try:
                # Step 1: Decompress the RTF data.
                rtf_data = decompress_rtf(compressed_data)

                # Step 2: Convert the decompressed RTF into HTML.
                html_content = convert_rtf_to_html(rtf_data)

                # Step 3: Update the database record.
                cursor.execute(
                    update_query,
                    html_content,
                    record_id
                )

                successful += 1

                logger.info(
                    "Processed record %s (%s/%s)",
                    record_id,
                    index,
                    total_records
                )

            except Exception:
                failed += 1

                logger.exception(
                    "Failed to process record %s",
                    record_id
                )

            # Commit changes periodically.
            if index % BATCH_SIZE == 0:
                connection.commit()

                logger.info(
                    "Progress: %s/%s records processed.",
                    index,
                    total_records
                )

        # Commit any remaining updates.
        connection.commit()

        logger.info("Conversion process completed.")
        logger.info("Successfully converted: %s", successful)
        logger.info("Failed records: %s", failed)

    except Exception:
        logger.exception("The conversion process encountered an error.")

        if connection:
            connection.rollback()

        raise

    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
