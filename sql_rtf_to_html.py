
"""
SQL Server RTF to HTML Converter
================================

Decompresses SQL Server compressed RTF data, converts it into HTML
using the external RTF2HTML executable, and updates SQL Server records.

Features:
    - Environment-based configuration
    - SQL identifier validation
    - Windows Integrated Authentication and SQL authentication
    - Streaming database retrieval using fetchmany()
    - Independent database transactions for each update
    - Automatic database reconnection and retry handling
    - Dry-run mode
    - Configurable conversion timeout
    - Conversion statistics and logging
    - Temporary file cleanup
    - Detection of extracted image assets

Requirements:
    pip install -r requirements.txt

Configuration:
    Copy .env.example to .env and configure the database settings.

Usage:
    python sql_rtf_to_html.py
    python sql_rtf_to_html.py --dry-run
"""

import argparse
import logging
import os
import re
import subprocess
import sys
import tempfile
import time

from dataclasses import dataclass
from pathlib import Path

import pyodbc

from compressed_rtf import decompress
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()


def get_required(name):
    """Retrieve a required environment variable."""

    value = os.getenv(name)

    if value is None or not value.strip():
        raise ValueError(
            f"Missing required configuration: {name}"
        )

    return value.strip()


def get_bool(name, default=False):
    """Parse a boolean environment variable."""

    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip().lower()

    if value in ("yes", "true", "1", "on"):
        return True

    if value in ("no", "false", "0", "off"):
        return False

    raise ValueError(
        f"Invalid boolean configuration: {name}={value}"
    )


def get_int(name, default, minimum=0):
    """Parse and validate an integer environment variable."""

    value = os.getenv(name, str(default))

    try:
        result = int(value)
    except ValueError:
        raise ValueError(
            f"{name} must be an integer."
        )

    if result < minimum:
        raise ValueError(
            f"{name} must be at least {minimum}."
        )

    return result


def get_float(name, default, minimum=0):
    """Parse and validate a floating-point environment variable."""

    value = os.getenv(name, str(default))

    try:
        result = float(value)
    except ValueError:
        raise ValueError(
            f"{name} must be a number."
        )

    if result < minimum:
        raise ValueError(
            f"{name} must be at least {minimum}."
        )

    return result


@dataclass
class Config:
    """Application configuration."""

    db_driver: str
    db_server: str
    db_name: str

    db_trusted_connection: bool
    db_username: str
    db_password: str

    db_encrypt: bool
    db_trust_server_certificate: bool

    db_table: str
    db_id_column: str
    db_source_column: str
    db_html_column: str

    rtf2html_exe: Path

    fetch_batch_size: int
    max_retries: int
    retry_delay_seconds: float

    connection_timeout: int
    conversion_timeout: int
    query_timeout: int

    dry_run: bool
    fail_on_extracted_images: bool

    log_file: str


def load_config():
    """Load and validate application configuration."""

    config = Config(
        db_driver=os.getenv(
            "DB_DRIVER",
            "ODBC Driver 18 for SQL Server"
        ).strip(),

        db_server=get_required("DB_SERVER"),
        db_name=get_required("DB_NAME"),

        db_trusted_connection=get_bool(
            "DB_TRUSTED_CONNECTION",
            True
        ),

        db_username=os.getenv("DB_USERNAME", "").strip(),

        # Do not strip passwords; whitespace may be intentional.
        db_password=os.getenv("DB_PASSWORD", ""),

        db_encrypt=get_bool("DB_ENCRYPT", True),

        db_trust_server_certificate=get_bool(
            "DB_TRUST_SERVER_CERTIFICATE",
            False
        ),

        db_table=get_required("DB_TABLE"),
        db_id_column=get_required("DB_ID_COLUMN"),
        db_source_column=get_required("DB_SOURCE_COLUMN"),
        db_html_column=get_required("DB_HTML_COLUMN"),

        rtf2html_exe=Path(
            get_required("RTF2HTML_EXE")
        ).expanduser(),

        fetch_batch_size=get_int(
            "FETCH_BATCH_SIZE",
            get_int("BATCH_SIZE", 100, minimum=1),
            minimum=1
        ),

        max_retries=get_int(
            "MAX_RETRIES",
            3
        ),

        retry_delay_seconds=get_float(
            "RETRY_DELAY_SECONDS",
            2.0
        ),

        connection_timeout=get_int(
            "DB_CONNECTION_TIMEOUT_SECONDS",
            15,
            minimum=1
        ),

        conversion_timeout=get_int(
            "RTF2HTML_TIMEOUT_SECONDS",
            120,
            minimum=1
        ),

        query_timeout=get_int(
            "DB_QUERY_TIMEOUT_SECONDS",
            0
        ),

        dry_run=get_bool("DRY_RUN", False),

        fail_on_extracted_images=get_bool(
            "FAIL_ON_EXTRACTED_IMAGES",
            True
        ),

        log_file=os.getenv(
            "LOG_FILE",
            "rtf_conversion.log"
        ).strip()
    )

    if not config.db_driver:
        raise ValueError("DB_DRIVER cannot be empty.")

    if not config.db_trusted_connection:
        if not config.db_username or not config.db_password:
            raise ValueError(
                "DB_USERNAME and DB_PASSWORD are required "
                "when DB_TRUSTED_CONNECTION=no."
            )

    if (
        config.db_id_column.lower()
        in (
            config.db_source_column.lower(),
            config.db_html_column.lower()
        )
    ):
        raise ValueError(
            "The ID column must be different from the "
            "source and destination columns."
        )

    if (
        config.db_source_column.lower()
        == config.db_html_column.lower()
    ):
        raise ValueError(
            "Source and destination columns must be different."
        )

    return config


# ============================================================
# LOGGING
# ============================================================

def setup_logging(log_file):
    """Configure file and console logging."""

    log_path = Path(log_file)

    if log_path.parent != Path("."):
        log_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(
                log_path,
                encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )


logger = logging.getLogger(__name__)


# ============================================================
# SQL IDENTIFIER VALIDATION
# ============================================================

def quote_identifier(identifier, allow_schema=False):
    """
    Validate and quote SQL Server identifiers.

    Table names may contain up to three parts:
        Table
        Schema.Table
        Database.Schema.Table

    Column names must be a single identifier.

    Arbitrary SQL expressions are not accepted.
    """

    parts = identifier.split(".")

    if allow_schema:
        if not 1 <= len(parts) <= 3:
            raise ValueError(
                f"Invalid table identifier: {identifier}"
            )
    elif len(parts) != 1:
        raise ValueError(
            f"Invalid column identifier: {identifier}"
        )

    pattern = r"[A-Za-z_][A-Za-z0-9_]*"

    for part in parts:
        if not re.fullmatch(pattern, part):
            raise ValueError(
                f"Invalid SQL identifier: {identifier}"
            )

    return ".".join(
        f"[{part}]" for part in parts
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

def odbc_escape(value):
    """
    Escape an ODBC connection string value.

    Braces protect special characters such as semicolons.
    """

    return "{" + str(value).replace("}", "}}") + "}"


def build_connection_string(config):
    """Build the SQL Server ODBC connection string."""

    parts = [
        f"DRIVER={odbc_escape(config.db_driver)}",
        f"SERVER={odbc_escape(config.db_server)}",
        f"DATABASE={odbc_escape(config.db_name)}",
        f"Encrypt={'yes' if config.db_encrypt else 'no'}",
        (
            "TrustServerCertificate="
            f"{'yes' if config.db_trust_server_certificate else 'no'}"
        )
    ]

    if config.db_trusted_connection:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(
            f"UID={odbc_escape(config.db_username)}"
        )
        parts.append(
            f"PWD={odbc_escape(config.db_password)}"
        )

    return ";".join(parts) + ";"


def create_connection(config, autocommit=True):
    """Create a SQL Server database connection."""

    return pyodbc.connect(
        build_connection_string(config),
        timeout=config.connection_timeout,
        autocommit=autocommit
    )


def create_cursor(connection, config):
    """Create a database cursor with the configured timeout."""

    cursor = connection.cursor()
    cursor.timeout = config.query_timeout

    return cursor


# ============================================================
# RTF DECOMPRESSION
# ============================================================

def decompress_rtf(compressed_data):
    """Decompress SQL Server compressed RTF data."""

    if compressed_data is None:
        raise ValueError(
            "Compressed RTF data cannot be NULL."
        )

    if isinstance(compressed_data, memoryview):
        compressed_data = compressed_data.tobytes()

    if not isinstance(compressed_data, bytes):
        compressed_data = bytes(compressed_data)

    if not compressed_data:
        raise ValueError(
            "Compressed RTF data is empty."
        )

    return decompress(compressed_data)


# ============================================================
# RTF TO HTML CONVERSION
# ============================================================

def convert_rtf_to_html(rtf_data, config):
    """
    Convert decompressed RTF into HTML using RTF2HTML.

    Temporary files are removed automatically.

    Note:
        RTF2HTML may extract embedded images into a separate
        .files directory. This script stores HTML text in SQL
        Server, but does not persist image assets.
    """

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_path = Path(temp_dir)

        rtf_file = temp_path / "input.rtf"
        html_file = temp_path / "output.html"

        # Write decompressed RTF data.
        if isinstance(rtf_data, str):
            rtf_data = rtf_data.encode("utf-8")

        rtf_file.write_bytes(rtf_data)

        # Execute the external converter.
        result = subprocess.run(
            [
                str(config.rtf2html_exe),
                str(rtf_file),
                str(html_file)
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=config.conversion_timeout,
            check=False
        )

        if result.returncode != 0:
            raise RuntimeError(
                "RTF2HTML conversion failed. "
                f"Exit code: {result.returncode}. "
                f"Output: {result.stderr.strip()[:1000]}"
            )

        if not html_file.is_file():
            raise FileNotFoundError(
                "RTF2HTML did not generate an HTML file."
            )

        html_data = html_file.read_bytes()

        if not html_data:
            raise ValueError(
                "RTF2HTML generated an empty HTML file."
            )

        # Detect extracted image assets.
        images_dir = Path(
            str(html_file) + ".files"
        )

        if images_dir.is_dir():
            image_files = [
                path for path in images_dir.rglob("*")
                if path.is_file()
            ]

            if image_files:
                message = (
                    f"RTF2HTML extracted {len(image_files)} "
                    "image asset(s), but this script does not "
                    "store image files in SQL Server."
                )

                if config.fail_on_extracted_images:
                    raise RuntimeError(
                        message + " Conversion was stopped to "
                        "avoid storing HTML with missing images."
                    )

                logger.warning(message)

        # Decode the generated HTML.
        try:
            html_content = html_data.decode("utf-8-sig")
        except UnicodeDecodeError:
            html_content = html_data.decode(
                "cp1252",
                errors="replace"
            )

        return html_content


# ============================================================
# DATABASE UPDATE
# ============================================================

def update_record(
    connection,
    config,
    update_query,
    html_content,
    record_id
):
    """
    Update one database record.

    Each update is committed independently through ODBC
    autocommit. This prevents a failed record from leaving
    a shared batch transaction in an uncertain state.

    Returns:
        True  - record updated
        False - record was no longer eligible for updating
    """

    cursor = None

    try:
        cursor = create_cursor(connection, config)

        cursor.execute(
            update_query,
            html_content,
            record_id
        )

        affected_rows = cursor.rowcount

        # A row count of zero means another process may have
        # populated the destination column since it was read.
        if affected_rows == 0:
            return False

        return True

    finally:
        if cursor:
            cursor.close()


def update_record_with_retry(
    connection,
    config,
    update_query,
    html_content,
    record_id
):
    """
    Attempt a database update with automatic reconnection.

    Returns:
        (connection, updated)
    """

    for attempt in range(config.max_retries + 1):

        try:
            updated = update_record(
                connection,
                config,
                update_query,
                html_content,
                record_id
            )

            return connection, updated

        except pyodbc.Error:

            logger.exception(
                "Database update failed. Attempt %s of %s.",
                attempt + 1,
                config.max_retries + 1
            )

            try:
                connection.close()
            except Exception:
                pass

            if attempt >= config.max_retries:
                raise

            delay = (
                config.retry_delay_seconds
                * (2 ** attempt)
            )

            logger.info(
                "Reconnecting to database in %.1f seconds.",
                delay
            )

            time.sleep(delay)

            connection = create_connection(
                config,
                autocommit=True
            )

    raise RuntimeError(
        "Database update failed after all retry attempts."
    )


# ============================================================
# PROCESSING STATISTICS
# ============================================================

@dataclass
class Statistics:
    records_seen: int = 0
    converted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0


def log_statistics(stats, start_time, dry_run):
    """Display processing statistics."""

    elapsed = time.perf_counter() - start_time

    rate = (
        stats.records_seen / elapsed
        if elapsed > 0
        else 0
    )

    logger.info("=" * 55)
    logger.info("CONVERSION SUMMARY")
    logger.info("=" * 55)

    logger.info(
        "Records examined: %s",
        stats.records_seen
    )

    logger.info(
        "Successfully converted: %s",
        stats.converted
    )

    logger.info(
        "Successfully updated: %s",
        stats.updated
    )

    logger.info(
        "Skipped records: %s",
        stats.skipped
    )

    logger.info(
        "Failed records: %s",
        stats.failed
    )

    logger.info(
        "Execution time: %.2f seconds",
        elapsed
    )

    logger.info(
        "Processing rate: %.2f records/second",
        rate
    )

    if dry_run:
        logger.info(
            "DRY-RUN MODE: No database records were updated."
        )

    logger.info("=" * 55)


# ============================================================
# MAIN PROCESSING
# ============================================================

def main(dry_run_override=False):

    config = load_config()

    setup_logging(config.log_file)

    dry_run = config.dry_run or dry_run_override

    # Validate the external executable before connecting.
    if not config.rtf2html_exe.is_file():
        raise FileNotFoundError(
            "RTF2HTML executable not found: "
            f"{config.rtf2html_exe}"
        )

    # Validate SQL identifiers.
    table = quote_identifier(
        config.db_table,
        allow_schema=True
    )

    id_column = quote_identifier(
        config.db_id_column
    )

    source_column = quote_identifier(
        config.db_source_column
    )

    html_column = quote_identifier(
        config.db_html_column
    )

    select_query = f"""
        SELECT
            {id_column},
            {source_column}
        FROM {table}
        WHERE
            {source_column} IS NOT NULL
            AND {html_column} IS NULL
    """

    update_query = f"""
        UPDATE {table}
        SET {html_column} = ?
        WHERE
            {id_column} = ?
            AND {html_column} IS NULL
    """

    stats = Statistics()
    start_time = time.perf_counter()

    reader_connection = None
    writer_connection = None

    reader_cursor = None

    logger.info("Starting SQL Server RTF to HTML conversion.")

    if dry_run:
        logger.info("DRY-RUN MODE ENABLED.")

    try:
        # Use separate connections for reading and writing.
        #
        # This allows the reader to keep its result set open
        # while the writer updates records without requiring
        # Multiple Active Result Sets (MARS).

        reader_connection = create_connection(
            config,
            autocommit=True
        )

        reader_cursor = create_cursor(
            reader_connection,
            config
        )

        if not dry_run:
            writer_connection = create_connection(
                config,
                autocommit=True
            )

        logger.info("Database connection established.")

        reader_cursor.arraysize = config.fetch_batch_size

        reader_cursor.execute(select_query)

        logger.info(
            "Retrieving records in batches of %s.",
            config.fetch_batch_size
        )

        while True:

            records = reader_cursor.fetchmany(
                config.fetch_batch_size
            )

            if not records:
                break

            for record in records:

                stats.records_seen += 1

                record_number = stats.records_seen

                record_id = record[0]
                compressed_data = record[1]

                try:
                    # Step 1: Decompress RTF.
                    rtf_data = decompress_rtf(
                        compressed_data
                    )

                    # Step 2: Convert RTF to HTML.
                    html_content = convert_rtf_to_html(
                        rtf_data,
                        config
                    )

                    stats.converted += 1

                    # Step 3: Update database.
                    if dry_run:
                        logger.info(
                            "Record %s converted successfully "
                            "(dry-run).",
                            record_number
                        )

                        continue

                    (
                        writer_connection,
                        updated
                    ) = update_record_with_retry(
                        writer_connection,
                        config,
                        update_query,
                        html_content,
                        record_id
                    )

                    if updated:
                        stats.updated += 1

                        logger.info(
                            "Record %s updated successfully.",
                            record_number
                        )

                    else:
                        stats.skipped += 1

                        logger.info(
                            "Record %s skipped: destination "
                            "was already populated.",
                            record_number
                        )

                except Exception:

                    stats.failed += 1

                    logger.exception(
                        "Failed to process record %s.",
                        record_number
                    )

            logger.info(
                "Progress: %s records examined.",
                stats.records_seen
            )

    except Exception:

        logger.exception(
            "The conversion process encountered a fatal error."
        )

        raise

    finally:

        if reader_cursor:
            reader_cursor.close()

        if reader_connection:
            reader_connection.close()

        if writer_connection:
            writer_connection.close()

        logger.info("Database connections closed.")

        log_statistics(
            stats,
            start_time,
            dry_run
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Decompress SQL Server compressed RTF data "
            "and convert it to HTML."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Convert records without updating SQL Server."
        )
    )

    args = parser.parse_args()

    try:
        main(
            dry_run_override=args.dry_run
        )

    except KeyboardInterrupt:
        logger.warning(
            "Process interrupted by user."
        )

        sys.exit(130)

    except Exception:
        logger.exception(
            "Application terminated due to an error."
        )

        sys.exit(1)
