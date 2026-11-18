
from pathlib import Path
from compressed_rtf import decompress
import subprocess
import tempfile
import pyodbc
import logging

# =====================================
# CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent
RTF2HTML_EXE = BASE_DIR / "rtf2html.exe"

# SQL Server connection
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=YourDatabase;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

TABLE_NAME = "[dbo].[YourTable]"
ID_COLUMN = "[YourIDColumn]"
SOURCE_COLUMN = "[YourCompressedRtfColumn]"
HTML_COLUMN = "[YourHtmlColumn]"

BATCH_SIZE = 50

# Logging
logging.basicConfig(
    filename=BASE_DIR / "rtf_conversion.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# =====================================
# STEP 1: CONVERT COMPRESSED DATA TO HTML
# =====================================

def convert_to_html(compressed_data):
    """
    Decompress SQL Server binary RTF data
    and convert it into HTML using rtf2html.exe.
    """

    if not isinstance(compressed_data, bytes):
        compressed_data = bytes(compressed_data)

    # Decompress LZFu data
    rtf_data = decompress(compressed_data)

    if not rtf_data:
        raise ValueError("RTF decompression returned empty data.")

    # Use temporary files for rtf2html.exe
    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = Path(temp_dir)

        input_rtf = temp_dir / "input.rtf"
        output_html = temp_dir / "output.html"

        input_rtf.write_bytes(rtf_data)

        # Run RTF to HTML conversion
        result = subprocess.run(
            [
                str(RTF2HTML_EXE),
                str(input_rtf),
                str(output_html)
            ],
            capture_output=True,
            text=True,
            check=True
        )

        if not output_html.is_file():
            raise RuntimeError(
                "RTF2HTML did not generate the expected HTML file. "
                f"Output: {result.stdout} "
                f"Errors: {result.stderr}"
            )

        html_data = output_html.read_bytes()

        if not html_data:
            raise ValueError("RTF2HTML generated an empty HTML file.")

        # Decode HTML into a Python string for SQL NVARCHAR
        try:
            return html_data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return html_data.decode("cp1252", errors="replace")


# =====================================
# STEP 2: CONNECT TO SQL SERVER
# =====================================

if not RTF2HTML_EXE.is_file():
    raise FileNotFoundError(
        f"RTF2HTML executable not found: {RTF2HTML_EXE}"
    )

connection = pyodbc.connect(CONNECTION_STRING)
cursor = connection.cursor()

print("Connected to SQL Server.")


# =====================================
# STEP 3: RETRIEVE RECORDS
# =====================================

select_sql = f"""
SELECT
    {ID_COLUMN},
    {SOURCE_COLUMN}
FROM {TABLE_NAME}
WHERE {SOURCE_COLUMN} IS NOT NULL
AND {HTML_COLUMN} IS NULL
ORDER BY {ID_COLUMN};
"""

cursor.execute(select_sql)
records = cursor.fetchall()

total_records = len(records)

print(f"Found {total_records} records to process.")


# =====================================
# STEP 4: UPDATE HTML COLUMN
# =====================================

update_sql = f"""
UPDATE {TABLE_NAME}
SET {HTML_COLUMN} = ?
WHERE {ID_COLUMN} = ?;
"""

success_count = 0
failed_count = 0

for index, record in enumerate(records, start=1):

    record_id = record[0]
    compressed_data = record[1]

    try:

        if not compressed_data:
            continue

        html_content = convert_to_html(compressed_data)

        cursor.execute(
            update_sql,
            html_content,
            record_id
        )

        success_count += 1

        print(
            f"[{index}/{total_records}] "
            f"Record ID {record_id}: SUCCESS"
        )

        # Commit periodically
        if success_count % BATCH_SIZE == 0:
            connection.commit()

    except Exception as error:

        failed_count += 1

        logging.exception(
            "Failed to process record ID %s",
            record_id
        )

        print(
            f"[{index}/{total_records}] "
            f"Record ID {record_id}: FAILED - {error}"
        )


# =====================================
# STEP 5: FINALISE
# =====================================

connection.commit()

cursor.close()
connection.close()

print("\n=====================================")
print("CONVERSION COMPLETED")
print("=====================================")
print(f"Total records: {total_records}")
print(f"Successful:    {success_count}")
print(f"Failed:        {failed_count}")
print("Log file:      rtf_conversion.log")
