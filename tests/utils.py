"""Test helpers."""

import base64

try:
    import fitz  # type: ignore  # pylint: disable=import-error
except ImportError:  # pragma: no cover
    fitz = None  # type: ignore


def generate_pdf(path):
    """Create a simple two-page PDF with images and captions."""

    if fitz is None:  # pragma: no cover - requires PyMuPDF
        raise RuntimeError("PyMuPDF is required to generate sample PDFs")

    doc = fitz.open()
    # The image used in the generated PDF is stored as a Base64 string.  In the
    # original version the string was split across two arguments to
    # ``base64.b64decode``.  Python treats the second bytes object as the
    # ``altchars`` parameter rather than part of the data, triggering an
    # ``AssertionError`` when decoding.  Concatenating the pieces into a single
    # bytes literal ensures the entire string is decoded correctly.
    img_bytes = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PsLK"
        b"FQAAAABJRU5ErkJggg=="
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

