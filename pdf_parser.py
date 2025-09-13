"""Utilities for extracting PDF data and building Foundry VTT scenes."""

import json
import re
from pathlib import Path
from typing import List

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None  # type: ignore


def _slugify(text):
    """Return *text* as a lowercase filename fragment."""

    slug = re.sub(r"[^0-9a-zA-Z]+", "_", text).strip("_").lower()
    return slug or "image"


def _find_nearby_text(page, rect, max_dist=20):
    """Return text closest to ``rect`` on ``page`` within ``max_dist``."""

    below = fitz.Rect(rect.x0, rect.y1, rect.x1, rect.y1 + max_dist)
    text = page.get_textbox(below).strip()
    if text:
        return text
    above = fitz.Rect(rect.x0, rect.y0 - max_dist, rect.x1, rect.y0)
    text = page.get_textbox(above).strip()
    return text or None


def _page_hierarchy(doc):
    """Map page numbers to a list of bookmarks representing their hierarchy."""

    hierarchy = {}
    toc = doc.get_toc(simple=False)
    index = 0
    stack: List[str] = []
    for page_num in range(1, doc.page_count + 1):
        while index < len(toc) and toc[index][2] == page_num:
            level, title, _ = toc[index][:3]
            stack = stack[: level - 1]
            stack.append(title)
            index += 1
        hierarchy[page_num] = list(stack)
    return hierarchy


def _image_label(page, img, idx, use_metadata):
    """Return a label for ``img`` on ``page``."""

    page_index, img_index = idx
    label = None
    if use_metadata and len(img) > 7 and img[7]:
        label = img[7]
        if re.fullmatch(r"(?:fzimg\d+|im\d+|image\d+)", label.lower()):
            label = None
    if use_metadata and not label:
        rect = page.get_image_bbox(img)
        label = _find_nearby_text(page, rect)
    if not label:
        label = f"p{page_index}_img{img_index}"
    return label


def _unique_name(label, used_names):
    """Return a unique slugified name for ``label``."""

    base = _slugify(label)
    candidate = base
    counter = 1
    while candidate in used_names:
        candidate = f"{base}_{counter}"
        counter += 1
    used_names.add(candidate)
    return candidate


def _process_page(page, page_index, folders, ctx, page_text=None):
    """Extract images from a single page."""

    use_metadata = ctx["use_metadata"]
    for img_index, img in enumerate(page.get_images(full=True), start=1):
        pix = fitz.Pixmap(page.parent, img[0])
        label = _image_label(page, img, (page_index, img_index), use_metadata)
        name = (
            f"{_unique_name(label, ctx['used_names'])}."
            f"{'png' if pix.alpha else 'jpg'}"
        )
        path = ctx["out_dir"] / name
        pix.save(path)
        img_data = {
            "name": name,
            "path": str(path),
            "width": pix.width,
            "height": pix.height,
            "page": page_index,
            "folders": folders if use_metadata else [],
        }
        if ctx.get("include_text") and page_text is not None:
            img_data["text"] = page_text
        ctx["images"].append(img_data)


def extract_images(pdf_path, out_dir, use_metadata=True, include_text=False):
    """Extract images from a PDF and save them to *out_dir*.

    Returns a list of dictionaries describing each extracted image with keys:
    ``name``, ``path``, ``width``, ``height``, ``page`` and ``folders``.
    When ``use_metadata`` is ``True`` image names attempt to use metadata or
    nearby text and page bookmarks supply folder hierarchy. Otherwise, names
    fall back to ``p{page}_img{index}`` and ``folders`` is empty. When
    ``include_text`` is ``True`` the full text of the source page is captured
    in a ``text`` field for each image.
    """

    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if fitz is None:  # pragma: no cover - requires PyMuPDF
        raise ImportError("PyMuPDF is required to extract images")

    doc = fitz.open(pdf_path)
    hierarchy = _page_hierarchy(doc) if use_metadata else {}
    images = []
    ctx = {
        "out_dir": out_dir,
        "images": images,
        "used_names": set(),
        "use_metadata": use_metadata,
        "include_text": include_text,
    }

    for page_index, page in enumerate(doc, start=1):
        page_text = page.get_text("text") if include_text else None
        _process_page(
            page,
            page_index,
            hierarchy.get(page_index, []),
            ctx,
            page_text=page_text,
        )
    return images


def extract_text(pdf_path):
    """Return a list with the text of each page."""
    if fitz is None:  # pragma: no cover - requires PyMuPDF
        raise ImportError("PyMuPDF is required to extract text")

    doc = fitz.open(pdf_path)
    return [page.get_text("text") for page in doc]


def _tokens(text):
    """Return a list of lowercase word tokens from *text*."""

    return re.findall(r"\w+", text.lower())


def build_foundry_scenes(images, grid_size=100, tags_from_text=False, note=None):
    """Build minimal Foundry VTT scene definitions for *images*.

    Each entry in *images* should be a dict as returned by ``extract_images``.
    When ``tags_from_text`` is ``True`` folder names and page text are used to
    populate a ``tags`` list on each scene. ``note`` sets a ``notes`` field on
    every scene when provided.
    """

    scenes = []
    for img in images:
        scene = {
            "name": img["name"],
            "img": img["path"],
            "width": img["width"],
            "height": img["height"],
            "grid": grid_size,
            "gridType": 1,
        }
        if img.get("folders"):
            scene["folder"] = "/".join(img["folders"])
        if tags_from_text:
            tags = []
            if img.get("folders"):
                tags.extend(f.lower() for f in img["folders"])
            if img.get("text"):
                tags.extend(_tokens(img["text"]))
            if tags:
                scene["tags"] = list(dict.fromkeys(tags))
        if note:
            scene["notes"] = note
        scenes.append(scene)
    return scenes


def main(argv: List[str] | None = None) -> None:
    """Command-line interface for :mod:`pdf_parser`."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Extract images and text from a PDF and prepare Foundry VTT scenes.",
    )
    parser.add_argument("pdf", help="Path to the source PDF file")
    parser.add_argument("out", help="Directory to store extracted images and JSON")
    parser.add_argument("--grid", type=int, default=100, help="Grid size for scenes")
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Use fallback names and ignore bookmarks for hierarchy",
    )
    parser.add_argument(
        "--tags-from-text",
        action="store_true",
        help="Generate scene tags from page text and bookmarks",
    )
    parser.add_argument("--note", help="Attach a note to every scene")
    args = parser.parse_args(argv)

    extracted_images = extract_images(
        args.pdf,
        args.out,
        use_metadata=not args.no_metadata,
        include_text=args.tags_from_text,
    )
    foundry_scenes = build_foundry_scenes(
        extracted_images,
        grid_size=args.grid,
        tags_from_text=args.tags_from_text,
        note=args.note,
    )

    output_dir = Path(args.out)
    json_path = output_dir / "scenes.json"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump({"scenes": foundry_scenes}, file, indent=2)

    print(
        f"Extracted {len(extracted_images)} images. Scene definitions saved to {json_path}"
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
