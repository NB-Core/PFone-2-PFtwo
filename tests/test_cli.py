"""Integration tests for the pdf_parser CLI."""

import json
from pathlib import Path
import subprocess
import sys

import pytest  # type: ignore  # pylint: disable=import-error

sys.path.append(str(Path(__file__).resolve().parent))
from utils import generate_pdf  # pylint: disable=wrong-import-position

pytest.importorskip("fitz")


def test_cli_integration(tmp_path):
    """Running the CLI extracts images and writes module & compendium files."""

    pdf = generate_pdf(tmp_path / "cli.pdf")
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

    module = json.loads((out / "module.json").read_text(encoding="utf-8"))
    assert module["title"] == "cli"

    pack = json.loads((out / "packs" / "images.json").read_text(encoding="utf-8"))
    assert len(pack) == 1
    assert "tags" in pack[0]
