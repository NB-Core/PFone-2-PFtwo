"""Tests for the :mod:`pdf_parser` module."""

from pathlib import Path
import sys

try:
    import pytest  # type: ignore
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

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
