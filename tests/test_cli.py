"""Integration tests for the pdf_parser CLI."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest  # type: ignore  # pylint: disable=import-error

sys.path.append(str(Path(__file__).resolve().parent))
from utils import generate_pdf  # pylint: disable=wrong-import-position

pytest.importorskip("fitz")


def test_cli_integration(tmp_path):
    """Running the CLI extracts images and writes scenes.json."""

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
        "--module-id",
        "testmod",
        "--title",
        "Test Title",
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    images = list(out.glob("*.png")) + list(out.glob("*.jpg"))
    assert len(images) == 1

    scenes = json.loads((out / "scenes.json").read_text(encoding="utf-8"))
    assert len(scenes["scenes"]) == 1
    assert "tags" in scenes["scenes"][0]

    module = json.loads((out / "module.json").read_text(encoding="utf-8"))
    assert module["name"] == "testmod"
    assert module["title"] == "Test Title"

    compendium = json.loads(
        (out / "packs" / "images.json").read_text(encoding="utf-8")
    )
    assert len(compendium) == 1


def test_env_overrides(tmp_path):
    """Environment variables override CLI flags."""

    pdf = generate_pdf(tmp_path / "env.pdf")
    out = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "pdf_parser.py"),
        str(pdf),
        str(out),
        "--module-id",
        "cliid",
        "--title",
        "Cli Title",
    ]
    env = os.environ.copy()
    env["PFPDF_MODULE_ID"] = "envmod"
    env["PFPDF_TITLE"] = "Env Title"
    subprocess.run(cmd, check=True, capture_output=True, env=env)

    module = json.loads((out / "module.json").read_text(encoding="utf-8"))
    assert module["name"] == "envmod"
    assert module["title"] == "Env Title"
