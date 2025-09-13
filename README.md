# PFone-2-PFtwo

This repository contains a PDF parser that extracts embedded images and builds a [Foundry VTT](https://foundryvtt.com/) `JournalEntry` compendium.

## Requirements

- Python 3.10 or 3.11

## Installation

Install the project and its dependencies with `pip`:

```bash
pip install .
```

## Usage

Run the parser from anywhere using the `pfpdf` command:

```bash
pfpdf path/to/file.pdf output_dir
```

Images are written to `output_dir`, and the directory will contain a `module.json` manifest and a `packs/images.json` compendium file ready for import into Foundry VTT.

The parser uses [PyMuPDF](https://pymupdf.readthedocs.io/) to extract images, deduplicates them using PDF metadata, and can be extended with additional processing as needed. Optional flags provide extra metadata for the generated entries and module manifest:

- `--module-id my-module` – set the module identifier (the manifest `name`).
- `--title "My Title"` – set the module manifest title.
- `--tags-from-text` – include page text and bookmarks as tags on each entry.
- `--note "Some note"` – attach a note to every generated entry.

Environment variables `PFPDF_MODULE_ID` and `PFPDF_TITLE` override the corresponding command-line options when set.

Example:

```bash
pfpdf file.pdf out --module-id my-module --title "My Module" --tags-from-text --note "GM only"
```

## Testing

Run the linter and test suite before submitting changes:

```bash
pylint pdf_parser.py
pytest
```

## Labeling and Folder Hierarchy

- **Metadata-based labeling:** Alt text and bookmark titles label each image. Duplicate metadata points to the same JournalEntry so repeated images are not duplicated.
- **Page+index fallback:** When no metadata is available, entries are named `page_<page>_<index>` to guarantee a stable label.
- **Nested folders:** Bookmark hierarchies create nested folders inside the compendium, preserving the structure of the original PDF.

## Sample Output

`module.json`

```json
{
  "name": "pf-images",
  "title": "PF Images",
  "version": "1.0.0",
  "compatibleCoreVersion": "13",
  "packs": [
    {
      "name": "images",
      "label": "Images",
      "path": "packs/images.json",
      "type": "JournalEntry"
    }
  ]
}
```

`packs/images.json`

```json
[
  {
    "_id": "abc123",
    "name": "Goblin Ambush",
    "folder": "Encounters/Goblins",
    "pages": [
      {
        "name": "Goblin Ambush",
        "type": "image",
        "image": {"src": "list/0.png"}
      }
    ]
  }
]
```


## Importing into Foundry VTT v13

1. Copy `module.json`, the `packs/` directory, and the extracted image files into Foundry's `Data/modules/<your-module>` folder.
2. Launch Foundry and enable the module from **Settings → Manage Modules**.
3. Open the **Compendium Packs** sidebar, locate the **Images** pack, and choose **Import All** or drag entries into your world.
4. Imported entries appear in nested folders mirroring the PDF's bookmark structure.

## Contributing

Before submitting changes, review [AGENTS.md](AGENTS.md) for the project's master plan, development guidelines, and hierarchy expectations.
