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

## RTF2HTML Features and Limitations

This project uses the RTF2HTML Converter (version 0.1 Alpha) as an external command-line utility.

The original converter supports several RTF-to-HTML conversion capabilities. However, the current Python implementation only integrates the core file conversion functionality.

### Currently Implemented

The following functionality is implemented in the Python script:

- **RTF Decompression:** Decompresses SQL Server compressed RTF binary data using the `compressed-rtf` library.
- **HTML Conversion:** Converts decompressed RTF documents into HTML using `rtf2html.exe`.
- **Temporary File Management:** Creates temporary RTF and HTML files during conversion.
- **Database Integration:** Automatically stores generated HTML content in the configured SQL Server destination column.
- **Batch Processing:** Processes multiple database records and commits successful updates periodically.
- **Error Handling:** Handles individual conversion failures without terminating the entire processing operation.
- **Logging:** Records conversion errors and processing information for troubleshooting.

### Available in RTF2HTML but Not Yet Integrated

The original RTF2HTML Converter provides additional functionality that is not currently exposed or implemented in this Python integration.

| Feature | Description | Implementation Status |
|---|---|---|
| Image Output Directory | Allows specifying a custom directory for extracted images through an optional third command-line argument. | Not implemented |
| Image Extraction | Supports outputting images associated with converted RTF documents into a separate directory. | Not integrated |
| Alternative Output Formats | Original documentation mentions that the generated HTML can be adapted towards XML/XHTML output. | Not implemented |
| Windows DLL Integration | The converter provides a DLL interface with development headers and sample programs. | Not implemented |
| Additional RTF Formatting | Supports various formatting features such as capitalization, invisible text, long spaces and hard page breaks. | Handled by the external converter |

**Note:** Some of these capabilities are supported internally by the original executable, but their availability and behaviour depend on the converter version and input document.

### Potential Future Improvements

The following enhancements could extend the functionality of this project:

- [ ] Support a configurable image output directory.
- [ ] Handle extracted images and associate them with the generated HTML.
- [ ] Support RTF documents containing embedded images.
- [ ] Add configurable conversion options.
- [ ] Improve processing efficiency for large database tables through pagination or key-based batching.
- [ ] Add more detailed conversion statistics.
- [ ] Implement validation of generated HTML output.
- [ ] Investigate alternative conversion engines for improved compatibility with modern RTF documents.

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

### Important Distinction

The Python script acts as an integration layer between SQL Server, the compressed RTF data, and the external RTF2HTML executable.

It does not independently implement the RTF parsing or HTML rendering functionality.

Consequently, the quality and completeness of the generated HTML depend partly on the capabilities and limitations of the external converter.

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
