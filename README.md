# SQL Server RTF to HTML Converter

A Python utility for decompressing SQL Server compressed Rich Text Format (RTF) data, converting it into HTML, and updating database records using an external RTF2HTML converter.

This project demonstrates database automation using Python, SQL Server integration, binary data decompression, and third-party document conversion tools.

## Features

- **SQL Server Integration:** Connects to Microsoft SQL Server using `pyodbc`.
- **RTF Decompression:** Decompresses SQL Server compressed RTF data using the `compressed-rtf` Python library.
- **HTML Conversion:** Converts decompressed RTF documents into HTML using the external RTF2HTML Converter.
- **Automated Database Updates:** Stores converted HTML content in a designated database column.
- **Batch Retrieval:** Retrieves database records in configurable batches using `fetchmany()`.
- **Independent Database Updates:** Commits each successful update independently to reduce the impact of individual record failures.
- **Database Retry Handling:** Attempts to reconnect and retry failed database update operations.
- **Dry-Run Mode:** Allows conversion testing without modifying database records.
- **Configuration Management:** Uses environment variables and a `.env` file for database and application settings.
- **Input Validation:** Validates database identifiers and configuration values.
- **Conversion Timeout:** Prevents the external converter from running indefinitely.
- **Image Detection:** Detects extracted image files and can stop processing to prevent saving HTML with missing image assets.
- **Logging and Statistics:** Records processing errors, execution details, and conversion statistics.

## How It Works

The conversion process follows these steps:

1. Loads and validates the application configuration.
2. Checks that the external RTF2HTML executable is available.
3. Establishes connections to the configured SQL Server database.
4. Retrieves records where the compressed RTF source column is not `NULL` and the destination HTML column is `NULL`.
5. Retrieves records in batches to reduce memory consumption.
6. Decompresses the binary RTF data using `compressed-rtf`.
7. Saves the decompressed content into a temporary `.rtf` file.
8. Executes the RTF2HTML Converter to generate an HTML file.
9. Checks for extracted image assets.
10. Reads and decodes the generated HTML content.
11. Updates the corresponding database record unless dry-run mode is enabled.
12. Logs processing results and generates a conversion summary.

## Project Structure

```text
sql-server-rtf-to-html/
│
├── sql_rtf_to_html.py
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── THIRD_PARTY_NOTICES.md
```

## Requirements

- Windows operating system for the supplied RTF2HTML executable workflow.
- Python 3.10 or later.
- Microsoft SQL Server.
- Microsoft ODBC Driver 18 for SQL Server.
- RTF2HTML Converter (version 0.1 Alpha).
- Python dependencies listed in `requirements.txt`.

The RTF2HTML executable must be obtained separately. It is not included in this repository.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/FalconerDelta/sql-server-rtf-to-html.git
cd sql-server-rtf-to-html
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example configuration file:

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

Edit `.env` and provide your SQL Server connection details, database table and column names, and RTF2HTML executable location.

Do not commit your `.env` file to GitHub. It may contain database credentials and infrastructure information.

### 5. Configure RTF2HTML

Obtain the RTF2HTML Converter executable separately and configure its location in `.env`.

Example:

```ini
RTF2HTML_EXE=C:/Tools/rtf2html/rtf2html.exe
```

Refer to [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the converter's attribution and licensing information.

### 6. Run the script

From the repository root:

```bash
python sql_rtf_to_html.py
```

Processing progress will be displayed in the terminal. Errors and execution details will also be recorded in the configured log file.

## Usage

### Normal conversion

```bash
python sql_rtf_to_html.py
```

Processes eligible records and updates the destination HTML column.

### Dry-run mode

```bash
python sql_rtf_to_html.py --dry-run
```

Runs the decompression and HTML conversion process without updating SQL Server records.

Dry-run mode is useful for testing the configuration and checking whether the external converter works before performing database updates.

It does not guarantee that every database update will succeed, as no actual updates are attempted.

## Configuration

The application is configured through environment variables in `.env`.

### Database connection

| Variable | Description |
|---|---|
| `DB_DRIVER` | SQL Server ODBC driver name |
| `DB_SERVER` | SQL Server hostname or instance |
| `DB_NAME` | Database name |
| `DB_TRUSTED_CONNECTION` | Enables Windows Integrated Authentication |
| `DB_USERNAME` | SQL Server username when using SQL authentication |
| `DB_PASSWORD` | SQL Server password when using SQL authentication |
| `DB_ENCRYPT` | Enables encrypted SQL Server connections |
| `DB_TRUST_SERVER_CERTIFICATE` | Controls SQL Server certificate validation |
| `DB_CONNECTION_TIMEOUT_SECONDS` | Database connection timeout |

### Database table and columns

| Variable | Description |
|---|---|
| `DB_TABLE` | Target database table, optionally including schema |
| `DB_ID_COLUMN` | Unique record identifier column |
| `DB_SOURCE_COLUMN` | Source compressed RTF column |
| `DB_HTML_COLUMN` | Destination HTML column |

The script validates configured SQL identifiers before using them in SQL statements. Database values are still parameterised separately.

### RTF2HTML settings

| Variable | Description |
|---|---|
| `RTF2HTML_EXE` | Full path to the RTF2HTML executable |
| `RTF2HTML_TIMEOUT_SECONDS` | Maximum time allowed for one conversion |
| `FAIL_ON_EXTRACTED_IMAGES` | Stops processing when extracted image files are detected |

### Processing settings

| Variable | Description |
|---|---|
| `FETCH_BATCH_SIZE` | Number of database records retrieved per batch |
| `BATCH_SIZE` | Legacy fallback for the fetch batch size when `FETCH_BATCH_SIZE` is not set |
| `MAX_RETRIES` | Number of additional database update attempts |
| `RETRY_DELAY_SECONDS` | Initial delay between database retry attempts |
| `DB_QUERY_TIMEOUT_SECONDS` | SQL query timeout; `0` means no query timeout |
| `DRY_RUN` | Enables dry-run mode through configuration |
| `LOG_FILE` | Log file location |

Refer to `.env.example` for the complete configuration template.

## Database Considerations

The target database table should contain:

- A unique identifier column.
- A source column containing SQL Server compressed RTF binary data.
- A destination column capable of storing HTML content.

The script retrieves records where:

- The source RTF column is not `NULL`.
- The destination HTML column is `NULL`.

This prevents records that already contain converted HTML from being processed again.

Recommended destination column type:

```sql
NVARCHAR(MAX)
```

The script uses a separate database connection for reading and writing. This allows the reader to retrieve batches while the writer updates records.

Each successful database update is committed independently. This means a failure on one record does not roll back previously completed updates.

The update statement also checks that the destination HTML column remains `NULL`. If another process has already populated it, the record is skipped.

**Important:** Always test against a development database or backup before processing production records.

## Error Handling and Logging

The script handles individual record failures without intentionally terminating the entire processing operation.

It provides:

- Terminal progress updates.
- Successful conversion and update counts.
- Failed and skipped record counts.
- Detailed exception logging.
- Database reconnection and retry attempts.
- Configurable database and conversion timeouts.
- Final execution time and processing rate.

Database update retries apply to database errors. RTF decompression and HTML conversion errors are logged as record failures and are not automatically retried.

A failed database operation may require investigation before the affected record can be processed again.

## Image Handling

The original RTF2HTML Converter can extract embedded images into a separate directory.

For example, converting:

```text
output.html
```

may produce:

```text
output.html.files/
```

The current Python implementation stores the generated HTML content in SQL Server but does not store the extracted image files or upload them to a separate location.

By default, `FAIL_ON_EXTRACTED_IMAGES=yes` prevents the script from updating a database record when extracted image files are detected.

This avoids silently storing HTML that may reference image files that are not available to the application displaying the HTML.

Setting `FAIL_ON_EXTRACTED_IMAGES=no` allows processing to continue, but image references may not work unless the extracted assets are managed separately.

## RTF2HTML Features and Limitations

This project uses the RTF2HTML Converter version 0.1 Alpha as an external command-line utility.

The Python script acts as an integration layer. It does not independently implement RTF parsing or HTML rendering.

### Currently Implemented

| Feature | Description |
|---|---|
| RTF Decompression | Decompresses SQL Server compressed RTF binary data using `compressed-rtf` |
| HTML Conversion | Converts decompressed RTF documents using `rtf2html.exe` |
| Temporary File Management | Creates and cleans up temporary RTF and HTML files |
| Database Integration | Updates the configured SQL Server destination column |
| Batch Retrieval | Retrieves database records using `fetchmany()` |
| Independent Updates | Commits successful database updates independently |
| Retry Handling | Reconnects and retries failed database update operations |
| Dry-Run Mode | Converts records without updating SQL Server |
| Timeout Handling | Applies a configurable timeout to external conversion |
| Image Detection | Detects extracted image assets and optionally stops processing |
| Logging and Statistics | Records processing errors, progress and execution statistics |

### External Converter Capabilities

The original RTF2HTML Converter provides additional functionality that is not fully exposed or managed by this Python integration.

| Feature | Description | Status |
|---|---|---|
| Image Output Directory | Allows a custom image directory through an optional third command-line argument | Not configurable through Python |
| Image Extraction | Extracts images associated with converted RTF documents | Handled by external converter; asset management not integrated |
| Windows DLL Integration | Provides a DLL interface with development headers and sample programs | Not implemented |
| Additional RTF Formatting | Handles formatting features such as capitalization, invisible text, long spaces and hard page breaks | Handled by external converter |

The original documentation mentions that its HTML output could be adapted towards XML/XHTML output. This would require changes to the converter itself and is not a supported configuration option in this project.

### Potential Future Improvements

- Support a configurable image output directory.
- Manage extracted images and associate them with generated HTML.
- Add support for storing or uploading embedded image assets.
- Add configurable conversion options.
- Implement key-based pagination for very large database tables.
- Add automated unit and integration tests.
- Add HTML output validation.
- Investigate alternative RTF-to-HTML conversion engines.

### Known Limitations of the Original Converter

The RTF2HTML Converter version 0.1 Alpha has documented limitations, including:

- Limited conversion of lists into native HTML list elements (`OL`, `UL`, `DL`).
- Some bullet symbols may not render correctly across different browsers.
- Incomplete compatibility with certain OpenOffice Writer RTF documents.
- Limited support for BMP and WMF image conversion.
- No paragraph border conversion.
- No table border or table cell size control.
- No page header or footer conversion.
- No hyperlink conversion.
- No automatic generation of HTML heading elements (`H1`, `H2`, etc.).

The original author also notes that version 0.1 Alpha was not thoroughly tested.

These limitations originate from the third-party converter and are not necessarily caused by the Python integration.

For further details, refer to [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Technologies Used

- Python
- Microsoft SQL Server
- pyodbc
- compressed-rtf
- python-dotenv
- RTF2HTML Converter
- Microsoft ODBC Driver 18 for SQL Server

## Development Acknowledgement

This project was developed with assistance from ChatGPT by OpenAI, which was used to support code development, documentation preparation, code refinement and project structuring.

The implementation was reviewed and adapted for its intended database automation workflow.

## Licence

The Python source code in this repository is released under the [MIT License](LICENSE).

The RTF2HTML Converter is a separate third-party component and remains subject to its original licence. Refer to [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for further information.

Python dependencies also remain subject to their respective licences.

---

This project is intended for educational, demonstration and database automation purposes.
