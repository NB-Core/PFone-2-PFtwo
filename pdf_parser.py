import json
from pathlib import Path
import fitz  # PyMuPDF


def extract_images(pdf_path, out_dir):
    """Extract images from a PDF and save them to *out_dir*.

    Returns a list of dictionaries describing each extracted image with
    keys: name, path, width, height, page.
    """
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

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

    parser = argparse.ArgumentParser(description="Extract images and text from a PDF and prepare Foundry VTT scenes.")
    parser.add_argument("pdf", help="Path to the source PDF file")
    parser.add_argument("out", help="Directory to store extracted images and JSON")
    parser.add_argument("--grid", type=int, default=100, help="Grid size for scenes")
    args = parser.parse_args()

    images = extract_images(args.pdf, args.out)
    scenes = build_foundry_scenes(images, grid_size=args.grid)

    out_dir = Path(args.out)
    json_path = out_dir / "scenes.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump({"scenes": scenes}, f, indent=2)

    print(f"Extracted {len(images)} images. Scene definitions saved to {json_path}")
