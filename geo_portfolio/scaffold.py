"""Scaffold a per-accession project from the EXISTING repository template.

This reuses ``templates/project_template/`` (the single source of truth) rather
than duplicating its contents, mirroring what ``scripts/new_project.R`` does:
copy the tree and substitute the ``GSEXXXXXX`` / ``ORGANISM_DB`` placeholders.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

PLACEHOLDER_FILES = ("SUITABILITY.md", "analysis.qmd", "README.md")


class ScaffoldError(RuntimeError):
    pass


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Walk up from *start* (or CWD) to find the repo root (has templates/project_template)."""
    p = (start or Path.cwd()).resolve()
    for cand in (p, *p.parents):
        if (cand / "templates" / "project_template").is_dir():
            return cand
    raise ScaffoldError(
        "Could not locate the repository (no templates/project_template found). "
        "Run from inside the GEO repository."
    )


def template_dir(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or find_repo_root()
    return root / "templates" / "project_template"


def scaffold_project(
    accession: str,
    out_dir: Path,
    organism_db: str = "org.Hs.eg.db",
    force: bool = False,
    repo_root: Optional[Path] = None,
) -> Path:
    """Copy the project template to *out_dir* and substitute placeholders."""
    out_dir = Path(out_dir)
    tmpl = template_dir(repo_root)

    if out_dir.exists():
        if not force:
            raise ScaffoldError(
                f"{out_dir} already exists. Use --force to overwrite (this replaces files in place)."
            )
        # Overwrite template-derived files but keep any extra user files.
    shutil.copytree(tmpl, out_dir, dirs_exist_ok=True)

    for fname in PLACEHOLDER_FILES:
        f = out_dir / fname
        if f.exists():
            txt = f.read_text(encoding="utf-8")
            txt = txt.replace("GSEXXXXXX", accession).replace("ORGANISM_DB", organism_db)
            f.write_text(txt, encoding="utf-8")
    return out_dir


def write_triage_into_project(
    out_dir: Path,
    markdown: str,
    json_text: str,
    accession: str,
    overwrite_suitability: bool = True,
) -> dict:
    """Place a generated triage report into a scaffolded project.

    The markdown becomes SUITABILITY.md (replacing the template placeholder) when
    ``overwrite_suitability`` is True; otherwise it is written to notes/. The JSON
    always goes to notes/ for downstream automation.
    """
    out_dir = Path(out_dir)
    notes = out_dir / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    written = {}

    if overwrite_suitability:
        (out_dir / "SUITABILITY.md").write_text(markdown, encoding="utf-8")
        written["suitability"] = str(out_dir / "SUITABILITY.md")
    else:
        target = notes / f"{accession}_triage.md"
        target.write_text(markdown, encoding="utf-8")
        written["suitability"] = str(target)

    json_path = notes / f"{accession}_triage.json"
    json_path.write_text(json_text, encoding="utf-8")
    written["json"] = str(json_path)
    return written
