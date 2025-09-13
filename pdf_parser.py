"""Utilities for extracting PDF data and building Foundry VTT scenes."""

import json
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None  # type: ignore


def extract_images(pdf_path, out_dir):
    """Extract images from a PDF and save them to *out_dir*.

    Returns a list of dictionaries describing each extracted image with
    keys: name, path, width, height, page.
    """
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if fitz is None:  # pragma: no cover - requires PyMuPDF
        raise ImportError("PyMuPDF is required to extract images")

    doc = fitz.open(pdf_path)
    images = []
    for page_index, page in enumerate(doc, start=1):
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            ext = "png" if pix.alpha else "jpg"
            name = f"p{page_index}_img{img_index}.{ext}"
            file_path = out_dir / name
            pix.save(file_path)
            images.append({
                "name": name,
                "path": str(file_path),
                "width": pix.width,
                "height": pix.height,
                "page": page_index,
            })
    return images


def extract_text(pdf_path):
    """Return a list with the text of each page."""
    if fitz is None:  # pragma: no cover - requires PyMuPDF
        raise ImportError("PyMuPDF is required to extract text")

    doc = fitz.open(pdf_path)
    return [page.get_text("text") for page in doc]


def build_foundry_scenes(images, grid_size=100):
    """Build minimal Foundry VTT scene definitions for *images*.

    Each entry in *images* should be a dict as returned by ``extract_images``.
    """
    scenes = []
    for img in images:
        scenes.append({
            "name": img["name"],
            "img": img["path"],
            "width": img["width"],
            "height": img["height"],
            "grid": grid_size,
            "gridType": 1,
        })
    return scenes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract images and text from a PDF and prepare Foundry VTT scenes."
    )
    parser.add_argument("pdf", help="Path to the source PDF file")
    parser.add_argument("out", help="Directory to store extracted images and JSON")
    parser.add_argument("--grid", type=int, default=100, help="Grid size for scenes")
    args = parser.parse_args()

    extracted_images = extract_images(args.pdf, args.out)
    foundry_scenes = build_foundry_scenes(extracted_images, grid_size=args.grid)

    output_dir = Path(args.out)
    json_path = output_dir / "scenes.json"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump({"scenes": foundry_scenes}, file, indent=2)

    print(
        f"Extracted {len(extracted_images)} images. Scene definitions saved to {json_path}"
    )
