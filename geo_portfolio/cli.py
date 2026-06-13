"""`geo` command-line interface for the GEO RNA-seq reanalysis portfolio."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .data import DataDownloadError, download_counts, raw_count_urls
from .fetch import GeoFetchError, fetch_soft, validate_accession
from .parse import parse_soft
from .report import build_record, to_json, to_markdown
from .runner import RunError, run_analysis
from .scaffold import ScaffoldError, scaffold_project, write_triage_into_project
from .suitability import assess, orgdb_for

TEMPLATE_MARKER = "Set the count-loading code for this dataset."


def _is_curated_qmd(project_dir: Path) -> bool:
    """True if analysis.qmd has been customized (template placeholder removed)."""
    qmd = Path(project_dir) / "analysis.qmd"
    if not qmd.exists():
        return False
    return TEMPLATE_MARKER not in qmd.read_text(encoding="utf-8")

app = typer.Typer(
    add_completion=False,
    help="Triage GEO accessions and orchestrate the existing R/Quarto reanalysis workflow.",
)
console = Console()
err_console = Console(stderr=True)

_CLASS_STYLE = {"suitable": "bold green", "manual_review": "bold yellow", "unsuitable": "bold red"}


def _parse_formats(fmt: str) -> List[str]:
    out = [f.strip().lower() for f in (fmt or "").split(",") if f.strip()]
    bad = [f for f in out if f not in ("markdown", "md", "json")]
    if bad:
        raise typer.BadParameter(f"Unknown format(s): {', '.join(bad)} (use markdown,json)")
    return ["markdown" if f == "md" else f for f in out] or ["markdown"]


def _triage_one(accession: str, cache_dir: str, refresh: bool):
    """Fetch + parse + assess. Returns (meta, suit, record)."""
    soft = fetch_soft(accession, cache_dir=cache_dir, refresh=refresh)
    meta = parse_soft(soft)
    suit = assess(meta)
    record = build_record(meta, suit)
    return meta, suit, record


def _write_reports(meta, suit, out_dir: Path, accession: str, formats: List[str]) -> List[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    if "markdown" in formats:
        p = out_dir / f"{accession}_triage.md"
        p.write_text(to_markdown(meta, suit), encoding="utf-8")
        written.append(str(p))
    if "json" in formats:
        p = out_dir / f"{accession}_triage.json"
        p.write_text(to_json(meta, suit), encoding="utf-8")
        written.append(str(p))
    return written


def _print_triage(record: dict) -> None:
    cls = record["suitability_class"]
    style = _CLASS_STYLE.get(cls, "white")
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column(justify="right", style="dim")
    table.add_column()
    table.add_row("accession", record["accession"])
    title = record["title"][:70] + ("…" if len(record["title"]) > 70 else "")
    table.add_row("title", title)
    table.add_row("organism", record["organism"])
    table.add_row("assay", record["assay_type"])
    table.add_row("samples", str(record["n_samples"]))
    table.add_row("raw counts", record["raw_counts_available"])
    table.add_row("normalized", record["normalized_values_present"])
    table.add_row("design", record["recommended_design"])
    table.add_row("DE method", record["de_method"])
    table.add_row("decision", f"[{style}]{record['decision']}[/{style}]")
    table.add_row("next", record["next_action"])

    console.print(Panel(
        table,
        title=f"[{style}]{cls.replace('_', ' ').upper()}[/{style}] · score {record['suitability_score']}/100",
        subtitle=record["accession"],
        border_style=style.split()[-1],
    ))
    for w in record["warnings"]:
        console.print(f"  [yellow]⚠[/yellow]  {w}")


def _summary_row(record: dict) -> dict:
    return {
        "accession": record["accession"],
        "title": record["title"],
        "organism": record["organism"],
        "n_samples": record["n_samples"],
        "raw_counts": record["raw_counts_available"],
        "suitability_class": record["suitability_class"],
        "score": record["suitability_score"],
        "decision": record["decision"],
        "warnings": " | ".join(record["warnings"]),
        "next_action": record["next_action"],
    }


# --------------------------------------------------------------------------- #
#  Commands
# --------------------------------------------------------------------------- #

@app.command()
def triage(
    accession: str = typer.Argument(..., help="GEO series accession, e.g. GSE157830"),
    out: Optional[Path] = typer.Option(None, "--out", help="Directory to write reports into"),
    fmt: str = typer.Option("markdown,json", "--format", help="Comma list: markdown,json"),
    refresh: bool = typer.Option(False, "--refresh", help="Bypass the metadata cache"),
    cache_dir: str = typer.Option(".geo_cache", "--cache-dir", help="Where to cache GEO SOFT"),
):
    """Triage a single GEO accession (suitability gate + transparent score)."""
    if not validate_accession(accession):
        err_console.print(f"[red]Invalid accession[/red] '{accession}' (expected like GSE123456).")
        raise typer.Exit(2)
    formats = _parse_formats(fmt)
    try:
        meta, suit, record = _triage_one(accession, cache_dir, refresh)
    except GeoFetchError as exc:
        err_console.print(f"[red]Fetch failed:[/red] {exc}")
        raise typer.Exit(1)

    _print_triage(record)
    if out is not None:
        written = _write_reports(meta, suit, out, accession, formats)
        for w in written:
            console.print(f"  [green]✓[/green] wrote {w}")


@app.command()
def batch(
    file: Path = typer.Argument(..., help="Text file: one GEO accession per line (# comments allowed)"),
    out: Path = typer.Option(Path("triage_reports"), "--out", help="Output directory"),
    fmt: str = typer.Option("markdown,json", "--format", help="Comma list: markdown,json"),
    refresh: bool = typer.Option(False, "--refresh", help="Bypass the metadata cache"),
    cache_dir: str = typer.Option(".geo_cache", "--cache-dir"),
):
    """Triage a batch of accessions; write per-accession reports + a summary table."""
    if not file.exists():
        err_console.print(f"[red]No such file:[/red] {file}")
        raise typer.Exit(2)
    formats = _parse_formats(fmt)
    accessions = []
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()   # drop full-line and inline comments
        if line:
            accessions.append(line)
    if not accessions:
        err_console.print("[red]No accessions found in input file.[/red]")
        raise typer.Exit(2)

    out.mkdir(parents=True, exist_ok=True)
    rows: List[dict] = []
    for acc in accessions:
        if not validate_accession(acc):
            console.print(f"[red]✗ {acc}[/red] — invalid accession, skipped")
            rows.append({"accession": acc, "title": "", "organism": "", "n_samples": "",
                         "raw_counts": "", "suitability_class": "error",
                         "score": "", "decision": "error", "warnings": "invalid accession",
                         "next_action": "fix accession"})
            continue
        try:
            meta, suit, record = _triage_one(acc, cache_dir, refresh)
            _write_reports(meta, suit, out, acc, formats)
            rows.append(_summary_row(record))
            style = _CLASS_STYLE.get(record["suitability_class"], "white").split()[-1]
            console.print(f"[{style}]●[/{style}] {acc}: {record['suitability_class']} "
                          f"(score {record['suitability_score']}) — {record['decision']}")
        except Exception as exc:  # keep going on any single-accession failure
            console.print(f"[red]✗ {acc}[/red] — {exc}")
            rows.append({"accession": acc, "title": "", "organism": "", "n_samples": "",
                         "raw_counts": "", "suitability_class": "error", "score": "",
                         "decision": "error", "warnings": str(exc), "next_action": "retry / inspect"})

    _write_batch_summary(rows, out)
    console.print(f"\n[green]✓[/green] {len(rows)} accessions → reports + summary in {out}/")


def _write_batch_summary(rows: List[dict], out: Path) -> None:
    cols = ["accession", "title", "organism", "n_samples", "raw_counts",
            "suitability_class", "score", "decision", "warnings", "next_action"]
    csv_path = out / "summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)
    md = ["# Triage batch summary", "",
          "| " + " | ".join(cols) + " |",
          "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        md.append("| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in cols) + " |")
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")


@app.command()
def scaffold(
    accession: str = typer.Argument(..., help="GEO series accession"),
    out: Optional[Path] = typer.Option(None, "--out", help="Project dir (default projects/<ACC>)"),
    org: Optional[str] = typer.Option(None, "--org", help="Organism annotation DB (e.g. org.Mm.eg.db)"),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing project"),
):
    """Scaffold a new project from the existing template (no analysis run)."""
    if not validate_accession(accession):
        err_console.print(f"[red]Invalid accession[/red] '{accession}'.")
        raise typer.Exit(2)
    out_dir = out or Path("projects") / accession
    try:
        scaffold_project(accession, out_dir, organism_db=org or "org.Hs.eg.db", force=force)
    except ScaffoldError as exc:
        err_console.print(f"[red]Scaffold failed:[/red] {exc}")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] scaffolded {out_dir} from templates/project_template")
    console.print(f"  next: edit {out_dir}/SUITABILITY.md, then `geo run {accession}`")


@app.command("init-project")
def init_project(
    accession: str = typer.Argument(..., help="GEO series accession"),
    out: Optional[Path] = typer.Option(None, "--out", help="Project dir (default projects/<ACC>)"),
    with_triage_report: bool = typer.Option(
        False, "--with-triage-report", help="Triage the accession and embed the report as SUITABILITY.md"),
    org: Optional[str] = typer.Option(None, "--org", help="Organism annotation DB override"),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing project"),
    refresh: bool = typer.Option(False, "--refresh"),
    cache_dir: str = typer.Option(".geo_cache", "--cache-dir"),
):
    """Scaffold a project and (optionally) embed a generated triage report."""
    if not validate_accession(accession):
        err_console.print(f"[red]Invalid accession[/red] '{accession}'.")
        raise typer.Exit(2)
    out_dir = out or Path("projects") / accession

    meta = suit = None
    organism_db = org or "org.Hs.eg.db"
    if with_triage_report:
        try:
            meta, suit, record = _triage_one(accession, cache_dir, refresh)
            organism_db = org or orgdb_for(meta)
            _print_triage(record)
        except GeoFetchError as exc:
            err_console.print(f"[red]Triage fetch failed:[/red] {exc}")
            raise typer.Exit(1)

    try:
        scaffold_project(accession, out_dir, organism_db=organism_db, force=force)
    except ScaffoldError as exc:
        err_console.print(f"[red]Scaffold failed:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] scaffolded {out_dir} (org={organism_db})")
    if with_triage_report and meta is not None:
        written = write_triage_into_project(out_dir, to_markdown(meta, suit), to_json(meta, suit), accession)
        for k, v in written.items():
            console.print(f"  [green]✓[/green] {k}: {v}")
        console.print(f"  decision: [bold]{suit.decision}[/bold] — review SUITABILITY.md before `geo run`.")


@app.command()
def run(
    accession: str = typer.Argument(..., help="GEO accession (project name)"),
    project: Optional[Path] = typer.Option(None, "--project", help="Project dir (default projects/<ACC>)"),
    env: str = typer.Option("geo-rnaseq", "--env", help="mamba environment name"),
    force: bool = typer.Option(False, "--force", help="Run even if triage is not 'include'"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the command without running"),
):
    """Run the existing R/Quarto analysis for a project (gated on triage)."""
    project_dir = project or Path("projects") / accession
    try:
        cmd = run_analysis(project_dir, env=env, force=force, dry_run=dry_run)
    except (RunError, Exception) as exc:
        if isinstance(exc, RunError):
            err_console.print(f"[red]Cannot run:[/red] {exc}")
            raise typer.Exit(1)
        raise
    if dry_run:
        console.print("[dim]dry-run, would execute:[/dim] " + " ".join(cmd))
    else:
        console.print(f"[green]✓[/green] rendered {project_dir}/analysis.qmd")


@app.command()
def data(
    accession: str = typer.Argument(..., help="GEO series accession"),
    project: Optional[Path] = typer.Option(None, "--project", help="Project dir (default projects/<ACC>)"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Re-download even if the file exists"),
    refresh: bool = typer.Option(False, "--refresh", help="Bypass the metadata cache"),
    cache_dir: str = typer.Option(".geo_cache", "--cache-dir"),
):
    """Download the raw count matrix GEO triage detected into the project's data/raw/."""
    if not validate_accession(accession):
        err_console.print(f"[red]Invalid accession[/red] '{accession}'.")
        raise typer.Exit(2)
    project_dir = project or Path("projects") / accession
    try:
        meta = parse_soft(fetch_soft(accession, cache_dir=cache_dir, refresh=refresh))
        paths = download_counts(meta, project_dir, overwrite=overwrite,
                                progress=lambda m: console.print(f"  [dim]{m}[/dim]"))
    except (GeoFetchError, DataDownloadError) as exc:
        err_console.print(f"[red]Data download failed:[/red] {exc}")
        raise typer.Exit(1)
    for p in paths:
        console.print(f"  [green]✓[/green] {p}")


@app.command()
def pipeline(
    accession: str = typer.Argument(..., help="GEO series accession"),
    out: Optional[Path] = typer.Option(None, "--out", help="Project dir (default projects/<ACC>)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing project (asks first)"),
    env: str = typer.Option("geo-rnaseq", "--env", help="mamba environment for the render"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the render command without running"),
    refresh: bool = typer.Option(False, "--refresh"),
    cache_dir: str = typer.Option(".geo_cache", "--cache-dir"),
):
    """End-to-end: triage → scaffold → download counts → run (one command).

    Conservative: stops at the triage gate for exclude/conditional, never
    overwrites a curated project without --force, and only auto-runs DESeq2 when
    the project's analysis.qmd has actually been customized.
    """
    if not validate_accession(accession):
        err_console.print(f"[red]Invalid accession[/red] '{accession}'.")
        raise typer.Exit(2)
    out_dir = out or Path("projects") / accession

    # 1) Triage.
    try:
        meta, suit, record = _triage_one(accession, cache_dir, refresh)
    except GeoFetchError as exc:
        err_console.print(f"[red]Fetch failed:[/red] {exc}")
        raise typer.Exit(1)
    _print_triage(record)

    # 2) Gate.
    if suit.decision == "exclude":
        err_console.print(f"[red]Stopping:[/red] {suit.next_action}")
        raise typer.Exit(1)
    if suit.decision == "conditional":
        console.print(f"[yellow]Conditional[/yellow] — {suit.next_action}")
        if not (yes or typer.confirm("Scaffold anyway (to document it), without running?", default=True)):
            raise typer.Exit(0)

    # 3) Scaffold (preserve an existing curated project unless --force).
    organism_db = orgdb_for(meta)
    exists = out_dir.exists()
    if exists and not force:
        console.print(f"[dim]Project {out_dir} already exists — keeping it (use --force to rebuild).[/dim]")
    else:
        if exists and force and not yes:
            if not typer.confirm(f"Overwrite template files in {out_dir}?", default=False):
                raise typer.Exit(0)
        try:
            scaffold_project(accession, out_dir, organism_db=organism_db, force=force)
            write_triage_into_project(out_dir, to_markdown(meta, suit), to_json(meta, suit), accession)
            console.print(f"  [green]✓[/green] scaffolded {out_dir} (org={organism_db})")
        except ScaffoldError as exc:
            err_console.print(f"[red]Scaffold failed:[/red] {exc}")
            raise typer.Exit(1)

    # 4) Download counts (safe; only when raw counts were detected).
    if raw_count_urls(meta):
        try:
            paths = download_counts(meta, out_dir, progress=lambda m: console.print(f"  [dim]{m}[/dim]"))
            for p in paths:
                console.print(f"  [green]✓[/green] data: {p}")
        except DataDownloadError as exc:
            console.print(f"  [yellow]⚠[/yellow] {exc}")
    else:
        console.print("  [yellow]⚠[/yellow] No raw-count file to download (FPKM-only or SRA/recount3).")

    # 5) Run, or guide.
    curated = _is_curated_qmd(out_dir)
    if suit.decision == "include" and curated:
        console.print("\n[bold]Running analysis…[/bold]")
        try:
            cmd = run_analysis(out_dir, env=env, dry_run=dry_run)
        except RunError as exc:
            err_console.print(f"[red]Run failed:[/red] {exc}")
            raise typer.Exit(1)
        console.print(("[dim]dry-run:[/dim] " + " ".join(cmd)) if dry_run
                      else f"[green]✓[/green] rendered {out_dir}/analysis.html")
    else:
        console.print("\n[bold]Next steps[/bold] (analysis needs curation before DESeq2):")
        console.print(f"  1. Edit [cyan]{out_dir}/analysis.qmd[/cyan] — count loading, design, contrast.")
        console.print(f"  2. Review [cyan]{out_dir}/SUITABILITY.md[/cyan].")
        console.print(f"  3. Run:  [cyan]geo run {accession}[/cyan]   (or re-run this pipeline).")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
):
    """geo — GEO RNA-seq reanalysis portfolio CLI."""
    if version:
        console.print(f"geo (geo_portfolio) {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


if __name__ == "__main__":
    app()
