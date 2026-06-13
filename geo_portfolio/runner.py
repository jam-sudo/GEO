"""Run the EXISTING R/Quarto analysis workflow for a scaffolded project.

This module does not analyze anything itself — it validates preconditions and
shells out to the existing pipeline (``quarto render`` inside the project's
mamba environment), refusing to proceed when triage says the dataset is
unsuitable.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

import yaml


class RunError(RuntimeError):
    pass


def read_decision(project_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """Return (decision, suitability_class) from the project's SUITABILITY.md, or (None, None)."""
    sf = Path(project_dir) / "SUITABILITY.md"
    if not sf.exists():
        return None, None
    text = sf.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, None
    _, _, rest = text.partition("---")
    fm, _, _ = rest.partition("\n---")
    try:
        data = yaml.safe_load(fm) or {}
    except yaml.YAMLError:
        return None, None
    return data.get("decision"), data.get("suitability_class")


def build_render_command(qmd: Path, env: str) -> List[str]:
    """Prefer running quarto inside the mamba env; fall back to bare quarto."""
    if shutil.which("mamba"):
        return ["mamba", "run", "-n", env, "quarto", "render", str(qmd)]
    if shutil.which("quarto"):
        return ["quarto", "render", str(qmd)]
    raise RunError(
        "Neither 'mamba' nor 'quarto' found on PATH. Build the environment first "
        "(make env) and activate it, or install Quarto."
    )


def run_analysis(
    project_dir: Path,
    env: str = "geo-rnaseq",
    force: bool = False,
    dry_run: bool = False,
) -> List[str]:
    """Validate preconditions and invoke the existing Quarto render.

    Returns the command that was (or would be) run. Raises RunError on refusal.
    """
    project_dir = Path(project_dir)
    qmd = project_dir / "analysis.qmd"
    if not project_dir.is_dir():
        raise RunError(f"Project folder not found: {project_dir}. Scaffold it first (geo scaffold).")
    if not qmd.exists():
        raise RunError(f"No analysis.qmd in {project_dir}. Scaffold the project first.")

    decision, cls = read_decision(project_dir)
    if decision is None:
        raise RunError(
            f"No usable SUITABILITY.md decision in {project_dir}. Run `geo triage {project_dir.name}` "
            "with --out into the project (or `geo init-project … --with-triage-report`) first."
        )
    if decision != "include" and not force:
        if decision == "conditional":
            raise RunError(
                f"Triage decision is 'conditional' ({cls}). Count-based DE is not valid yet — "
                "curate the data (e.g. obtain raw counts from recount3/SRA) and update SUITABILITY.md, "
                "then re-run. Use --force only if you know the counts are valid."
            )
        raise RunError(
            f"Triage decision is '{decision}' ({cls}). Refusing to run count-based DE on an "
            "unsuitable dataset. (Override with --force, not recommended.)"
        )

    cmd = build_render_command(qmd, env)
    if dry_run:
        return cmd
    subprocess.run(cmd, check=True)
    return cmd
