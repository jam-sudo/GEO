# `geo` — command-line interface

`geo` is the orchestration layer for this GEO RNA-seq reanalysis portfolio. It
**triages** GEO accessions (suitability gate + transparent score), generates
markdown/JSON reports in the repo's existing `SUITABILITY.md` schema, **scaffolds**
projects from the existing `templates/project_template/`, and **runs** the
existing R/Quarto analysis — without reimplementing any analysis logic.

## Install

```bash
# from the repository root
python -m venv .venv && source .venv/bin/activate
pip install -e .            # add ".[test]" for the test deps
geo --help
```

The console script is exactly `geo` (defined in `pyproject.toml`:
`geo = "geo_portfolio.cli:app"`).

## Commands

| Command | Purpose |
|---------|---------|
| **`geo pipeline <ACC>`** | **One command: triage → scaffold → download counts → run** |
| `geo triage <ACC>` | Triage one accession; print summary, optionally write reports |
| `geo batch <file>` | Triage many accessions; per-accession reports + summary CSV/MD |
| `geo data <ACC>` | Download the detected raw-count file into `data/raw/` |
| `geo scaffold <ACC>` | Create a project from the existing template |
| `geo init-project <ACC> --with-triage-report` | Scaffold + embed a generated triage report as `SUITABILITY.md` |
| `geo run <ACC>` | Render the existing `analysis.qmd` (refuses unless triage = `include`) |

### `geo pipeline` — the one-command workflow

```bash
geo pipeline GSE157830           # triage → scaffold → download counts → run, with prompts
geo pipeline GSE157830 --yes     # no prompts
geo pipeline GSE157830 --dry-run # show the render command instead of running
```

Collapses the whole flow into one command, but stays conservative:

- **Stops at the gate** for `exclude` (and asks before scaffolding a `conditional`).
- **Auto-downloads** the raw-count file triage detected (gene-level preferred); for FPKM-only/microarray it says so instead.
- **Never overwrites a curated project** without `--force` (which still asks first).
- **Only auto-runs DESeq2 when `analysis.qmd` has been curated** (the template placeholder removed). For a freshly scaffolded project it prints the curation steps instead of running a meaningless template.

So for an already-curated dataset, `geo pipeline <ACC>` is a true one-shot
reproduce; for a new dataset it does the mechanical setup and hands off the
scientific curation.

### `geo data` — fetch the count matrix

```bash
geo data GSE157830                       # into projects/GSE157830/data/raw/
geo data GSE157830 --project some/dir --overwrite
```

Downloads the series supplementary file(s) that triage classified as raw counts
(never FPKM/TPM). Errors clearly when GEO has no raw-count file (e.g. FPKM-only
deposits like GSE78220 — use recount3 instead).

### `geo triage`

```bash
geo triage GSE157830
geo triage GSE157830 --out examples/reports/GSE157830 --format markdown,json
```

- Fetches GEO metadata via two lightweight SOFT calls (`targ=self`, `targ=gsm`) and caches them under `.geo_cache/`.
- Inspects title, summary, organism, platform, sample characteristics, and supplementary files.
- Classifies the dataset as **suitable** (`include`), **manual review** (`conditional`), or **unsuitable** (`exclude`).
- Detects raw counts vs FPKM/TPM/RPKM/normalized/microarray.
- Infers factors (treatment, genotype, disease, timepoint, tissue, batch, cell line) from characteristics; **ambiguous labels are flagged, not guessed**.
- Produces a transparent 0–100 score with per-reason deltas.

### `geo batch`

```bash
geo batch examples/accessions.txt --out examples/reports --format markdown,json
```

- One accession per line; blank lines and `#` comments ignored.
- Continues past any single-accession failure.
- Writes `<ACC>_triage.md` / `<ACC>_triage.json` per accession plus `summary.csv` and `summary.md`
  (accession, title, organism, sample count, raw-count detection, suitability class, score, warnings, next action).

### `geo scaffold` / `geo init-project`

```bash
geo scaffold GSE157830 --out projects/GSE157830
geo init-project GSE157830 --out projects/GSE157830 --with-triage-report
```

- Copies `templates/project_template/` (the existing skeleton: `SUITABILITY.md`, `analysis.qmd`, `README.md`, `data/`, `results/figures`, `results/tables`, `scripts/`, `notes/`).
- Substitutes `GSEXXXXXX` / `ORGANISM_DB` (same placeholders as `scripts/new_project.R`).
- `--with-triage-report` triages the accession, auto-detects the organism DB, and writes the generated report as `SUITABILITY.md` (+ JSON in `notes/`).
- Refuses to overwrite an existing project unless `--force`.

### `geo run`

```bash
geo run GSE157830 --project projects/GSE157830
geo run GSE157830 --dry-run        # show the command without executing
```

- Reads the project's `SUITABILITY.md` decision.
- **Refuses** to run count-based DE unless the decision is `include` (conditional/exclude are blocked; `--force` overrides, not recommended).
- Invokes the existing pipeline: `mamba run -n geo-rnaseq quarto render projects/<ACC>/analysis.qmd`.

## How triage connects to the existing workflow

The triage markdown uses the **same YAML front-matter schema** as the
hand-written `projects/*/SUITABILITY.md`, so the existing
`scripts/build_triage.R` aggregates CLI-generated reports into `docs/TRIAGE.md`
unchanged. Scaffolding reuses the existing template; `geo run` calls the existing
Quarto/DESeq2 analysis. The CLI adds orchestration, not a second analysis stack.

Recommended portfolio loop:

```bash
# Fast path — one command does triage + scaffold + data download, then guides:
geo pipeline GSE123456

#   ... curate projects/GSE123456/analysis.qmd (count loading, design, contrast) ...

Rscript scripts/build_triage.R                            # refresh docs/TRIAGE.md
geo pipeline GSE123456                                    # now auto-runs (curated + include)
```

Or step by step (`triage` → `init-project` → `data` → `run`) if you prefer
explicit control — see the command table above.

## Scientific constraints (enforced)

- Never claims DESeq2 compatibility unless a raw **count** file is detected.
- Never treats FPKM/TPM/RPKM/normalized values as DESeq2 input (flags `conditional`).
- Never infers treatment/control from vague titles — only from `characteristics_ch1` fields; unmapped/ambiguous factors are marked.
- Microarray and single-cell are flagged as not directly DESeq2-compatible.
- When uncertain, returns **manual review required**.

## Limitations

- Triage is **metadata-only**: it does not download or inspect the actual count values (so it cannot detect, e.g., RSEM fractional counts — that check lives in the R `run_deseq2()` guard at analysis time).
- Factor inference is heuristic; always review the report before scaffolding/running.
- `geo run` requires the `geo-rnaseq` mamba environment (see `environment/environment.yml`).
