"""Integration tests for the pdf_parser CLI."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest  # type: ignore  # pylint: disable=import-error

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))
from utils import generate_pdf  # pylint: disable=wrong-import-position
import pdf_parser  # pylint: disable=wrong-import-position,import-error

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
    assert entry["pages"][0]["src"] == images[0].name


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
    assert len(pack) == 1
    assert pack[0]["name"].startswith("label_1")
    assert pack[0]["folder"] == "Section 1/Subsection 1.1"


def test_cli_no_metadata(tmp_path):
    """Fallback names are used and folders are empty when metadata is ignored."""

    pdf = generate_pdf(tmp_path / "nometa.pdf")
    out = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "pdf_parser.py"),
        str(pdf),
        str(out),
        "--no-metadata",
        "--pages",
        "1-1",
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    images = list(out.glob("*.png")) + list(out.glob("*.jpg"))
    assert len(images) == 1
    assert images[0].name.startswith("p1_img1")

    pack_dir = out / "packs"
    pack = json.loads((pack_dir / "images.json").read_text(encoding="utf-8"))
    assert list(pack_dir.iterdir()) == [pack_dir / "images.json"]
    entry = pack[0]
    assert entry["name"].startswith("p1_img1")
    assert "folder" not in entry


def test_cli_note(tmp_path):
    """Notes are attached to compendium entries when provided."""

    pdf = generate_pdf(tmp_path / "note.pdf")
    out = tmp_path / "out"
    note = "Remember the traps"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "pdf_parser.py"),
        str(pdf),
        str(out),
        "--note",
        note,
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    pack = json.loads((out / "packs" / "images.json").read_text(encoding="utf-8"))
    assert pack[0]["notes"] == note


def test_invalid_pages_range():
    """An invalid page range causes the CLI to exit with an error."""

    with pytest.raises(SystemExit) as exc:
        pdf_parser.main(["dummy.pdf", "out", "--pages", "invalid"])


@pytest.mark.parametrize("page_spec", ["5-2", "1-", "3"])
def test_reversed_or_malformed_pages_range(page_spec):
    """Reversed or malformed page ranges exit with an error."""

    with pytest.raises(SystemExit):
        pdf_parser.main(["dummy.pdf", "out", "--pages", page_spec])
