"""Tests for the :mod:`pdf_parser` module."""

from pathlib import Path
import sys

import pytest  # type: ignore  # pylint: disable=import-error

pytest.importorskip("fitz")

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from pdf_parser import (  # pylint: disable=wrong-import-position
    build_foundry_scenes,
    extract_images,
    extract_text,
)

from utils import generate_pdf  # pylint: disable=wrong-import-position


def test_build_foundry_scenes():
    """Verify scenes include image metadata, tags and notes."""
    images = [
        {
            "name": "map.png",
            "path": "maps/map.png",
            "width": 100,
            "height": 200,
            "text": "Dungeon Map",
            "folders": ["Dungeon"],
        }
    ]
    scenes = build_foundry_scenes(
        images, grid_size=75, tags_from_text=True, note="Check traps"
    )
    scene = scenes[0]
    assert scene["name"] == "map.png"
    assert scene["img"] == "maps/map.png"
    assert scene["width"] == 100
    assert scene["height"] == 200
    assert scene["grid"] == 75
    assert scene["gridType"] == 1
    assert scene["tags"] == ["dungeon", "map"]
    assert scene["notes"] == "Check traps"


def test_extract_images(tmp_path):
    """Ensure image extraction returns an empty list for PDFs without images."""
    pdf = Path(__file__).parent / "data" / "sample.pdf"
    images = extract_images(pdf, tmp_path)
    assert len(images) == 0


def test_extract_images_with_text(tmp_path):
    """Text of each page is captured when requested."""
    pdf = generate_pdf(tmp_path / "text.pdf")
    out = tmp_path / "out"
    images = extract_images(pdf, out, include_text=True)
    assert "text" in images[0]
    assert "Label 1" in images[0]["text"]


def test_extract_text():
    """Extracted text should contain sample content."""
    pdf = Path(__file__).parent / "data" / "sample.pdf"
    texts = extract_text(pdf)
    assert len(texts) == 1
    assert "Hello World" in texts[0]


def test_labels_and_hierarchy(tmp_path):
    """Images derive names from captions and folders from bookmarks."""

    pdf = generate_pdf(tmp_path / "labeled.pdf")
    out = tmp_path / "out"
    images = extract_images(pdf, out)
    assert images[0]["name"].startswith("label_1")
    assert images[0]["folders"] == ["Section 1"]
    assert images[1]["folders"] == ["Section 2"]

    out2 = tmp_path / "out2"
    images_nometa = extract_images(pdf, out2, use_metadata=False)
    assert images_nometa[0]["name"].startswith("p1_img1")
    assert images_nometa[0]["folders"] == []


def test_metadata_tagging(tmp_path):
    """Tags derive from folders and page text when requested."""

    pdf = generate_pdf(tmp_path / "tags.pdf")
    out = tmp_path / "out"
    images = extract_images(pdf, out, include_text=True)
    scenes = build_foundry_scenes(images, tags_from_text=True)
    tags = scenes[0]["tags"]
    assert "section 1" in tags
    assert "label" in tags


def test_extract_images_page_range(tmp_path):
    """Only pages within the provided range are processed."""

    pdf = generate_pdf(tmp_path / "range.pdf")
    out = tmp_path / "out"
    images = extract_images(pdf, out, page_range=(2, 2))
    assert len(images) == 1
    assert images[0]["page"] == 2

