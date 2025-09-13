"""Integration tests for the pdf_parser CLI."""

from pathlib import Path
import json
import subprocess
import sys

import pytest

try:
    import fitz  # type: ignore  # pylint: disable=import-error
except ImportError:  # pragma: no cover
    fitz = None  # type: ignore

pytest.importorskip("fitz")

import base64


def _generate_pdf(path):
    """Create a simple PDF with an image and caption on two pages."""

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


def test_cli_integration(tmp_path):
    """Running the CLI extracts images and writes scenes.json."""

    pdf = _generate_pdf(tmp_path / "cli.pdf")
    out = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "pdf_parser.py"),
        str(pdf),
        str(out),
        "--pages",
        "1-1",
        "--tags-from-text",
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    images = list(out.glob("*.png")) + list(out.glob("*.jpg"))
    assert len(images) == 1

    scenes = json.loads((out / "scenes.json").read_text(encoding="utf-8"))
    assert len(scenes["scenes"]) == 1
    assert "tags" in scenes["scenes"][0]
