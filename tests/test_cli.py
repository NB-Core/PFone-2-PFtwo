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
        "--module-id",
        "custom",
        "--title",
        "Custom",
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    images = list(out.glob("*.png")) + list(out.glob("*.jpg"))
    assert len(images) == 1

    module = json.loads((out / "module.json").read_text(encoding="utf-8"))
    assert module["name"] == "custom"
    assert module["title"] == "Custom"

    pack = json.loads((out / "packs" / "images.json").read_text(encoding="utf-8"))
    assert len(pack) == 1
    entry = pack[0]
    assert "tags" in entry
    assert entry["flags"]["pfpdf"]["module_id"] == "custom"
    assert entry["flags"]["pfpdf"]["title"] == "Custom"


def test_env_overrides(tmp_path):
    """Environment variables override CLI flags."""

    pdf = generate_pdf(tmp_path / "env.pdf")
    out = tmp_path / "out"
    env = os.environ.copy()
    env["PFPDF_MODULE_ID"] = "env_id"
    env["PFPDF_TITLE"] = "Env Title"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "pdf_parser.py"),
        str(pdf),
        str(out),
        "--module-id",
        "cli_id",
        "--title",
        "Cli Title",
    ]
    subprocess.run(cmd, check=True, capture_output=True, env=env)

    module = json.loads((out / "module.json").read_text(encoding="utf-8"))
    assert module["name"] == "env_id"
    assert module["title"] == "Env Title"

    pack = json.loads((out / "packs" / "images.json").read_text(encoding="utf-8"))
    flags = pack[0]["flags"]["pfpdf"]
    assert flags["module_id"] == "env_id"
    assert flags["title"] == "Env Title"


def test_cli_hierarchy(tmp_path):
    """CLI populates module and compendium with hierarchy data."""

    pdf = generate_pdf(tmp_path / "hier.pdf")
    out = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "pdf_parser.py"),
        str(pdf),
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    module = json.loads((out / "module.json").read_text(encoding="utf-8"))
    assert module["name"] == "hier"
    assert module["title"] == "hier"
    assert module["packs"][0]["type"] == "JournalEntry"

    pack = json.loads((out / "packs" / "images.json").read_text(encoding="utf-8"))
    assert len(pack) == 2
    assert pack[0]["name"].startswith("label_1")
    assert pack[0]["folder"] == "Section 1/Subsection 1.1"
    assert pack[1]["folder"] == "Section 2"
