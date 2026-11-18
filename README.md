# SQL Server RTF to HTML Converter

A Python-based utility for decompressing SQL Server compressed Rich Text Format (RTF) data, converting it into HTML, and automatically updating database records.

This project demonstrates database automation using Python, SQL Server integration, binary data decompression, and third-party document conversion tools.

## Features

- **SQL Server Integration:** Connects to Microsoft SQL Server using `pyodbc`.
- **RTF Decompression:** Decompresses SQL Server compressed RTF data using the `compressed-rtf` Python library.
- **HTML Conversion:** Converts decompressed RTF documents into HTML using the external RTF2HTML Converter.
- **Automated Database Updates:** Stores converted HTML content in a designated database column.
- **Batch Processing:** Processes multiple records and commits database updates periodically.
- **Error Handling:** Handles individual conversion failures without stopping the entire process.
- **Logging:** Records processing errors and execution details for troubleshooting.
- **Configurable Settings:** Supports custom database connections, table names, column names, and converter locations.

## How It Works

The conversion process follows these steps:

1. Establishes a connection to the configured SQL Server database.
2. Retrieves records containing compressed RTF data where the destination HTML column is `NULL`.
3. Decompresses the binary RTF data.
4. Saves the decompressed content into a temporary `.rtf` file.
5. Executes the RTF2HTML Converter to generate an HTML file.
6. Reads the generated HTML content.
7. Updates the corresponding database record.
8. Commits successful updates periodically.
9. Logs unsuccessful conversions for further investigation.

## Project Structure

```text
sql-server-rtf-to-html/
│
├── README.md
├── LICENSE
├── THIRD_PARTY_NOTICES.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── src/
│   └── convert_rtf.py
│
└── tools/
    └── README.md
```

## Requirements

- Windows operating system (for the supplied executable workflow).
- Python 3.10 or later.
- Microsoft SQL Server.
- Microsoft ODBC Driver 18 for SQL Server.
- RTF2HTML Converter (version 0.1 Alpha).
- Python dependencies listed in `requirements.txt`.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/sql-server-rtf-to-html.git

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

```powershell
Copy-Item .env.example .env
```

Update `.env` with your SQL Server connection details, database objects, and RTF2HTML executable location.

Do not commit your `.env` file to GitHub, as it may contain sensitive database credentials or infrastructure information.

### 5. Configure RTF2HTML

Obtain the RTF2HTML Converter executable separately and configure its location in `.env`.

Example:

```dotenv
RTF2HTML_EXE=C:/Tools/rtf2html/rtf2html.exe
```

The executable is not included in this repository. Refer to [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for its attribution and licensing information.

### 6. Run the script

From the repository root:

```bash
python src/convert_rtf.py
```

Processing progress will be displayed in the terminal, while errors and execution details will be recorded in the log file.

## Configuration

The following environment variables are available:

| Variable | Description |
|---|---|
| `DB_DRIVER` | SQL Server ODBC driver |
| `DB_SERVER` | SQL Server hostname or instance |
| `DB_NAME` | Database name |
| `DB_TRUSTED_CONNECTION` | Enables Windows authentication |
| `DB_USERNAME` | SQL Server username (if applicable) |
| `DB_PASSWORD` | SQL Server password (if applicable) |
| `DB_TRUST_SERVER_CERTIFICATE` | SQL Server certificate setting |
| `DB_TABLE` | Target database table |
| `DB_ID_COLUMN` | Unique record identifier |
| `DB_SOURCE_COLUMN` | Source compressed RTF column |
| `DB_HTML_COLUMN` | Destination HTML column |
| `RTF2HTML_EXE` | Path to the RTF2HTML executable |
| `BATCH_SIZE` | Number of successful updates between commits |
| `LOG_FILE` | Log file location |

Refer to `.env.example` for the complete configuration template.

## Database Considerations

The target database table should contain:

- A unique identifier column.
- A source column containing compressed RTF binary data.
- A destination column capable of storing HTML content.

The script retrieves records where:

- The source RTF column is not `NULL`.
- The destination HTML column is `NULL`.

This prevents records that already have converted HTML content from being processed again.

**Recommended destination column type:** `NVARCHAR(MAX)`.

Always test against a development database or backup before processing production records.

## Error Handling and Logging

Individual conversion failures are logged and do not prevent subsequent records from being processed.

The script provides:

- Terminal progress updates.
- Successful and failed record counts.
- Detailed exception logging.
- Periodic database commits.

## Limitations

- Designed for SQL Server compressed RTF data compatible with the `compressed-rtf` Python library.
- Requires an external RTF2HTML executable.
- Uses temporary files during conversion.
- Retrieves matching records into memory before processing, which may require modification for very large datasets.
- The RTF2HTML executable must support the input and output command-line arguments used by the script.

## Technologies Used

- Python
- Microsoft SQL Server
- pyodbc
- compressed-rtf
- python-dotenv
- RTF2HTML Converter
- Windows ODBC Driver

## Development Acknowledgement

This project was developed with assistance from **ChatGPT by OpenAI**, which was used to support code development, documentation preparation, code refinement, and project structuring.

The implementation was reviewed and adapted for its intended database automation workflow.

## Licence

The Python source code in this repository is released under the [MIT License](LICENSE).

The RTF2HTML Converter is a separate third-party component and remains subject to its original licence. Refer to [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for further information.

---

*This project is intended for educational, demonstration, and database automation purposes.*
