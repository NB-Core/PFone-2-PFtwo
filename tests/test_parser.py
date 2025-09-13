"""Tests for the :mod:`pdf_parser` module."""

from pathlib import Path
import sys
import base64

try:
    import pytest  # type: ignore
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

try:
    import fitz  # type: ignore  # pylint: disable=import-error
except ImportError:  # pragma: no cover
    fitz = None  # type: ignore

sys.path.append(str(Path(__file__).resolve().parents[1]))

if pytest is not None:  # pragma: no branch
    pytest.importorskip("fitz")

from pdf_parser import (  # pylint: disable=wrong-import-position
    build_foundry_scenes,
    extract_images,
    extract_text,
)


def test_build_foundry_scenes():
    """Verify scenes include image metadata and grid size."""
    images = [{"name": "map.png", "path": "maps/map.png", "width": 100, "height": 200}]
    scenes = build_foundry_scenes(images, grid_size=75)
    assert scenes[0]["name"] == "map.png"
    assert scenes[0]["img"] == "maps/map.png"
    assert scenes[0]["width"] == 100
    assert scenes[0]["height"] == 200
    assert scenes[0]["grid"] == 75
    assert scenes[0]["gridType"] == 1


def test_extract_images(tmp_path):
    """Ensure image extraction returns an empty list for PDFs without images."""
    pdf = Path(__file__).parent / "data" / "sample.pdf"
    images = extract_images(pdf, tmp_path)
    assert len(images) == 0


def test_extract_text():
    """Extracted text should contain sample content."""
    pdf = Path(__file__).parent / "data" / "sample.pdf"
    texts = extract_text(pdf)
    assert len(texts) == 1
    assert "Hello World" in texts[0]


def _generate_pdf(path):
    """Create a simple PDF with images, captions and bookmarks."""

    doc = fitz.open()
    img_bytes = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PsLK"
        b"FQAAAABJRU5ErkJggg==",
    )
    toc = []
    for idx in range(2):
        page = doc.new_page()
        rect = fitz.Rect(20, 20, 120, 120)
        page.insert_image(rect, stream=img_bytes)
        page.insert_text(fitz.Point(20, 130), f"Label {idx + 1}")
        toc.append([1, f"Section {idx + 1}", idx + 1])
    doc.set_toc(toc)
    doc.save(path)
    return path


def test_labels_and_hierarchy(tmp_path):
    """Images derive names from captions and folders from bookmarks."""

    pdf = _generate_pdf(tmp_path / "labeled.pdf")
    out = tmp_path / "out"
    images = extract_images(pdf, out)
    assert images[0]["name"].startswith("label_1")
    assert images[0]["folders"] == ["Section 1"]
    assert images[1]["folders"] == ["Section 2"]

    out2 = tmp_path / "out2"
    images_nometa = extract_images(pdf, out2, use_metadata=False)
    assert images_nometa[0]["name"].startswith("p1_img1")
    assert images_nometa[0]["folders"] == []
