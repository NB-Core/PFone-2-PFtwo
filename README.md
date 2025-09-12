# PFone-2-PFtwo

This repository contains a simple PDF parser that extracts embedded images and
builds minimal [Foundry VTT](https://foundryvtt.com/) scene definitions.

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the parser:
   ```bash
   python pdf_parser.py path/to/file.pdf output_dir
   ```
   This will save images into `output_dir` and create a `scenes.json` file with
   basic scene definitions you can import into Foundry.

The parser uses [PyMuPDF](https://pymupdf.readthedocs.io/) to extract images and
can be extended with additional metadata or text extraction as needed.

