"""Utilities for extracting PDF data and building Foundry VTT compendiums."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

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

    for img_index, img in enumerate(page.get_images(full=True), start=1):
        label = _image_label(page, img, (page_index, img_index), ctx["use_metadata"])
        xref = img[0]
        if xref in ctx["seen_xrefs"]:
            ctx["labels"].setdefault(label, ctx["seen_xrefs"][xref]["name"])
            continue

        pix = fitz.Pixmap(page.parent, xref)
        try:
            checksum = hashlib.md5(pix.tobytes()).hexdigest()
            if checksum in ctx["seen_checksums"]:
                ctx["seen_xrefs"][xref] = ctx["seen_checksums"][checksum]
                ctx["labels"].setdefault(
                    label, ctx["seen_checksums"][checksum]["name"]
                )
                continue

            name = (
                f"{_unique_name(label, ctx['used_names'])}."
                f"{'png' if pix.alpha else 'jpg'}"
            )
            pix.save(ctx["out_dir"] / name)
            img_data = {
                "name": name,
                "path": name,
                "width": pix.width,
                "height": pix.height,
                "page": page_index,
                "folders": folders if ctx["use_metadata"] else [],
            }
            if ctx.get("include_text") and page_text is not None:
                img_data["text"] = page_text
        finally:
            getattr(pix, "close", lambda: None)()

        ctx["images"].append(img_data)
        ctx["seen_xrefs"][xref] = img_data
        ctx["seen_checksums"][checksum] = img_data
        ctx["labels"].setdefault(label, name)


def extract_images(
    pdf_path,
    out_dir,
    use_metadata=True,
    include_text=False,
    page_range: Optional[Tuple[int, int]] = None,
):
    """Extract images from a PDF and save them to *out_dir*.

    Returns a tuple ``(images, labels)`` where ``images`` is a list of
    dictionaries describing each saved image and ``labels`` maps metadata
    labels to the corresponding image name. Each image dictionary contains
    ``name``, ``path`` (the relative filename), ``width``, ``height``, ``page``
    and ``folders``. When
    ``use_metadata`` is ``True`` image names attempt to use metadata or nearby
    text and page bookmarks supply folder hierarchy. Otherwise, names fall back
    to ``p{page}_img{index}`` and ``folders`` is empty. When ``include_text`` is
    ``True`` the full text of the source page is captured in a ``text`` field
    for each image. ``page_range`` may be a tuple of ``(start, end)`` page
    numbers limiting extraction to that inclusive range. Duplicate images are
    identified by xref or checksum and only saved once.
    """

    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if fitz is None:  # pragma: no cover - requires PyMuPDF
        raise ImportError("PyMuPDF is required to extract images")

    with fitz.open(pdf_path) as doc:
        hierarchy = _page_hierarchy(doc) if use_metadata else {}
        images: List[dict] = []
        ctx = {
            "out_dir": out_dir,
            "images": images,
            "used_names": set(),
            "use_metadata": use_metadata,
            "include_text": include_text,
            "seen_xrefs": {},
            "seen_checksums": {},
            "labels": {},
        }

        for page_index, page in enumerate(doc, start=1):
            if page_range and not page_range[0] <= page_index <= page_range[1]:
                continue
            page_text = page.get_text("text") if include_text else None
            _process_page(
                page,
                page_index,
                hierarchy.get(page_index, []),
                ctx,
                page_text=page_text,
            )
    return images, ctx["labels"]


def extract_text(pdf_path):
    """Return a list with the text of each page."""
    if fitz is None:  # pragma: no cover - requires PyMuPDF
        raise ImportError("PyMuPDF is required to extract text")

    with fitz.open(pdf_path) as doc:
        return [page.get_text("text") for page in doc]


def _tokens(text):
    """Return a list of lowercase word tokens from *text*."""

    return re.findall(r"\w+", text.lower())


def build_compendium_entries(
    images,
    tags_from_text: bool = False,
    note: str | None = None,
    module_id: str | None = None,
    title: str | None = None,
    image_dir: str | Path | None = None,
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """Build JournalEntry definitions for *images*.

    Each entry in *images* should be a dict as returned by ``extract_images``.
    When ``tags_from_text`` is ``True`` folder names and page text are used to
    populate a ``tags`` list on each entry. ``note`` sets a ``notes`` field on
    every entry when provided. ``module_id`` and ``title`` are stored as flags
    when supplied. ``image_dir`` optionally prefixes the image path for the
    ``src`` field, keeping the path relative for portability.
    """

    entries = []
    for img in images:
        src_path = str(Path(image_dir) / img["path"]) if image_dir else img["path"]
        entry = {
            "name": img["name"],
            "pages": [
                {
                    "name": img["name"],
                    "type": "image",
                    "src": src_path,
                }
            ],
        }
        if img.get("folders"):
            entry["folder"] = "/".join(img["folders"])
        if tags_from_text:
            tags = []
            if img.get("folders"):
                tags.extend(f.lower() for f in img["folders"])
            if img.get("text"):
                tags.extend(_tokens(img["text"]))
            if tags:
                entry["tags"] = list(dict.fromkeys(tags))
        if note:
            entry["notes"] = note
        if module_id or title:
            meta: dict[str, str] = {}
            if module_id:
                meta["module_id"] = module_id
            if title:
                meta["title"] = title
            entry["flags"] = {"pfpdf": meta}
        entries.append(entry)
    return entries


def main(argv: List[str] | None = None) -> None:
    """Command-line interface for :mod:`pdf_parser`."""

    parser = argparse.ArgumentParser(
        description="Extract images and text from a PDF and prepare a Foundry VTT compendium.",
    )
    parser.add_argument("pdf", help="Path to the source PDF file")
    parser.add_argument("out", help="Directory to store extracted images and JSON")
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Use fallback names and ignore bookmarks for hierarchy",
    )
    parser.add_argument(
        "--pages",
        help="Page range to extract, e.g. '2-5'",
    )
    parser.add_argument(
        "--tags-from-text",
        action="store_true",
        help="Generate entry tags from page text and bookmarks",
    )
    parser.add_argument("--note", help="Attach a note to every entry")
    parser.add_argument(
        "--module-id",
        help="Module identifier for the manifest (defaults to PDF filename)",
    )
    parser.add_argument(
        "--title",
        help="Module title for the manifest (defaults to PDF filename)",
    )
    args = parser.parse_args(argv)

    page_range = None
    if args.pages:
        try:
            page_range = tuple(map(int, args.pages.split("-", 1)))
            if len(page_range) != 2:
                raise ValueError
        except ValueError as exc:  # pragma: no cover - args parsing
            raise SystemExit("Invalid --pages format. Use START-END.") from exc
        if page_range[0] > page_range[1]:
            raise SystemExit("--pages start must be <= end.")

    extracted_images, _ = extract_images(
        args.pdf,
        args.out,
        use_metadata=not args.no_metadata,
        include_text=args.tags_from_text,
        page_range=page_range,
    )

    module_id = os.getenv(
        "PFPDF_MODULE_ID", args.module_id or _slugify(Path(args.pdf).stem)
    )
    title = os.getenv("PFPDF_TITLE", args.title or Path(args.pdf).stem)

    compendium_entries = build_compendium_entries(
        extracted_images,
        tags_from_text=args.tags_from_text,
        note=args.note,
        module_id=module_id,
        title=title,
    )

    output_dir = Path(args.out)
    pack_path = output_dir / "packs" / "images.json"
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    pack_path.write_text(
        json.dumps(compendium_entries, indent=2), encoding="utf-8"
    )

    module_data = {
        "name": module_id,
        "title": title,
        "packs": [
            {
                "name": "images",
                "label": "Images",
                "path": "packs/images.json",
                "type": "JournalEntry",
            }
        ],
    }
    (output_dir / "module.json").write_text(
        json.dumps(module_data, indent=2), encoding="utf-8"
    )

    print(
        f"Extracted {len(extracted_images)} images. Compendium saved to {pack_path}"
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point

    main()
