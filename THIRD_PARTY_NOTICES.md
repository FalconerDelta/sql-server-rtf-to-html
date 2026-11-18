# Third-Party Software Notices

This project uses third-party software for RTF document conversion. The following information acknowledges the original software author, copyright ownership, licensing conditions, and technical limitations.

---

## 1. RTF 2 HTML Converter

### Software Information

| Property | Details |
|---|---|
| Software | RTF 2 HTML Converter |
| Version | 0.1 Alpha |
| Author | Sergey A. Galin |
| Copyright | © 2001–2002 Sergey A. Galin |
| Homepage | [http://sergey-galin.chat.ru](http://sergey-galin.chat.ru) |
| Software Type | RTF-to-HTML command-line converter |
| Original Language | C++ |

### Description

The RTF 2 HTML Converter is a standalone utility developed by Sergey A. Galin for converting Rich Text Format (RTF) documents into HTML.

It generates HTML 4 and CSS2 output and is designed to preserve the appearance and formatting of the original RTF document as closely as possible.

Its documented features include:

- Compact HTML and CSS output.
- Support for various RTF formatting features.
- Font formatting, capitalization, invisible text, and long spaces.
- Support for hard page breaks.
- HTML comments for information that cannot be represented directly in HTML.
- Low memory usage and portable C++ implementation.
- Command-line execution and potential integration into other applications.

### Usage in This Project

This project uses the compiled Windows command-line executable (`rtf2html.exe`) as an external dependency.

The executable performs the conversion of decompressed RTF documents into HTML.

The command-line interface follows the original documented syntax:

```bash
rtf2html <input RTF file> <output HTML file> [<image output directory>]
```

The Python application invokes the converter using temporary input and output files.

The executable is not developed, modified, or maintained by this project.

### Original End-User Licence

The following licence conditions are reproduced from the original software documentation:

> This is a free software, you can redistribute and use it in compiled form at no charge. Modification of program executable and read-me files is not allowed.
>
> This program provided "AS IS" without warranty of any kind, whether express or implied. Use it at your own risk.
>
> When RTF2HTML is distributed as a part of another application, the application should contain a note in its About dialog, help printout (or provide the information in another sensible way), notifying users that RTF2HTML was used as a part of the application, and containing Author's name, copyright and home page URL, as provided in this document above.
>
> Note: If you want to buy program sources, please contact the author.

**Original copyright notice:**

Copyright © Sergey A. Galin, 2001–2002.

Homepage: [http://sergey-galin.chat.ru](http://sergey-galin.chat.ru)

### Distribution and Licensing Conditions

Based on the original documentation:

- The compiled executable may be used and redistributed at no charge.
- Modification of the executable is not permitted.
- Modification of the original README files is not permitted.
- The original author's name, copyright notice, and homepage URL must be provided when the converter is distributed as part of another application.
- The software is provided without warranty.

This project does not claim ownership of the RTF2HTML Converter or its original source code.

### Supported Platforms

According to the original documentation, the converter was written in standard C++ and was designed to be portable across multiple platforms.

Documented builds include:

- Linux command-line executable.
- Windows command-line executable.
- Windows DLL with development headers and sample programs.
- DOS command-line executable.

The Windows command-line executable is the version used by this project.

### Technical Limitations

The original documentation identifies several partially supported and unimplemented RTF features.

Examples include:

- Limited list and bullet conversion.
- Incomplete support for certain OpenOffice Writer RTF documents.
- Limited image conversion support.
- Unsupported vector image conversion.
- Missing paragraph and table border support.
- No page header or footer conversion.
- No hyperlink conversion.
- No HTML heading tag generation.

The original documentation also identifies version 0.1 Alpha as an early release that had not been thoroughly tested.

As a result, HTML output may vary depending on the source RTF document and its formatting.

Users should validate converted HTML before relying on it in production environments.

### Version Information

The original README documents:

- **Version 0.1 Alpha:** Initial release.
- **Version 0.2:** Introduced additional features, including improved OpenOffice compatibility, text indentation, crash fixes, and Unicode RTF support.

This project references the version 0.1 Alpha executable. The version 0.2 information is included for historical reference only and does not imply that this project uses that release.

### Copyright and Ownership

All rights to the RTF 2 HTML Converter remain with its original author, Sergey A. Galin.

This project is independently developed and is not affiliated with, endorsed by, or maintained by Sergey A. Galin.

---

## 2. Python Dependencies

This project also uses the following third-party Python libraries:

| Dependency | Purpose | Project |
|---|---|---|
| `pyodbc` | SQL Server database connectivity | [GitHub](https://github.com/mkleehammer/pyodbc) |
| `compressed-rtf` | Decompression of SQL Server compressed RTF data | [PyPI](https://pypi.org/project/compressed-rtf/) |
| `python-dotenv` | Environment variable configuration | [GitHub](https://github.com/theskumar/python-dotenv) |

Each dependency remains subject to its respective licence and copyright terms.

Please refer to the original project repositories and package documentation for their licensing information.

---

## 3. Development Acknowledgement

This project was developed with assistance from **ChatGPT by OpenAI**.

ChatGPT was used to assist with Python code development, code refinement, troubleshooting, documentation preparation, and repository structuring.

The use of ChatGPT does not imply any ownership of, affiliation with, or endorsement by OpenAI of the third-party software identified in this document.

---

## 4. Project Licence

The original Python source code developed for this repository is released under the MIT License.

The MIT License applies only to the original project code. It does not replace, modify, or override the licences or copyright terms of third-party software.

For further information, refer to the repository's [LICENSE](LICENSE) file.

---

**Third-party copyright notices are provided for attribution and licensing transparency.**
