# AGENTS

## Master Plan
1. **Environment**
   - Python ≥ 3.10, PyMuPDF
   - End tests: pytest, pylint
2. **Image Extraction & Labeling**
   - Iterate pages of PF1e PDF, export every image.
   - Deduplicate images via metadata (alt text, bookmarks); fallback `{page}_{index}`.
   - Generate metadata file (bookmarks headings, page numbers) and labeling dictionary.
3. **Foundry Compendium Generation (JournalEntry only)**
   - Produce `module.json`; `"title"` derived from PDF filename and `"name"` from CLI or sanitized filename.
   - Create a JournalEntry compendium (`packs/journal5e` or `.db`) containing one entry per labeled image.
   - Each entry's image `src` uses `list[index].png` and metadata supplies hierarchy.
   - Assign to nested folders when metadata supplies hierarchy.
4. **CLI Enhancements**
   - Flags: `--module-id`, `--title`, `--no-metadata`.
   - Layout: main module entry followed by extracted image file reference.
   - Environment variables override flags when present.
5. **Testing & Validation**
   - Unit tests: run CLI on a sample PDF and verify `module.json` and compendium content.
   - Integration tests: run CLI on a sample PDF and verify folder hierarchy, module, and compendium.
6. **Documentation & Project Guidance**
   - Expanded `README` describing usage, tests, folder hierarchy, and Foundry import steps.
   - Root `AGENTS.md` summarizing this master plan for contributors.

## Development Guidelines
- Write clear, well-documented Python code following PEP 8 style guidelines.
- Include or update tests for any code changes and run `pytest` before committing.
- Use conventional commit messages (e.g., `feat:`, `fix:`, `docs:`) and keep commits focused.

## Hierarchy Expectations
- The repository maintainer reviews and merges pull requests.
- Open an issue or discussion before starting work on significant changes.
- Contributors are expected to follow these guidelines and respect maintainers' decisions.
