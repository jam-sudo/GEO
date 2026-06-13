# A careful public RNA-seq reanalysis workflow

This repository is a **reproducible framework for reanalyzing public GEO RNA-seq
datasets** — built to demonstrate judgment, not just to produce plots. Every
dataset is *triaged before it is touched*: a standardized suitability report
decides whether the data can support a correct differential-expression analysis
at all, and **only datasets that pass are analyzed**.

> **Author:** jam-sudo

The emphasis, in order:

1. **Dataset triage** — a written, comparable suitability report per accession; some datasets are *excluded*, with reasons.
2. **Reproducibility** — one pinned environment, scripted runs, embedded `sessionInfo()`.
3. **Correct statistical design** — explicit design formulas; no DESeq2 on normalized values; replication checked before modelling.
4. **Biological interpretation** — results read in light of the underlying biology, not just thresholded gene lists.
5. **Limitations & assumptions** — documented honestly for every dataset.
6. **Comparison across reanalyses** — a cross-dataset triage table makes the judgments comparable at a glance.

## Start here: the triage table

👉 **[`docs/TRIAGE.md`](docs/TRIAGE.md)** — every dataset's suitability verdict
(include / conditional / exclude) in one comparison table, generated from each
project's machine-readable suitability record.

## How a dataset moves through the framework

```
GEO accession
   │
   ▼
[1] Suitability report  ──►  projects/<ACC>/SUITABILITY.md
   │   organism · assay · files · raw counts? · normalized? · replicates ·
   │   metadata clarity · possible contrasts · recommended design · decision
   │
   ├─ decision: exclude / conditional ──►  documented, NO DESeq2 forced
   │
   ▼ decision: include
[2] Reproducible DE analysis  ──►  projects/<ACC>/analysis.qmd
       QC · explicit-design DESeq2 · volcano/MA/heatmap · enrichment ·
       interpretation · limitations
```

The triage step is metadata-only (it doesn't even need R), so suitability is
decided from evidence — file inventory, value ranges, `characteristics` fields —
*before* committing to an analysis.

## Repository structure

```
├── README.md                      # this file
├── .gitattributes                 # keep rendered HTML out of GitHub language stats
├── docs/
│   ├── TRIAGE.md                  # cross-dataset comparison (the headline)
│   ├── triage.csv                 # machine-readable triage table
│   ├── cli.md                     # full `geo` CLI reference
│   └── README.md                  # methodology & conventions
├── Makefile                       # make triage / env / new / render
├── environment/environment.yml    # pinned R + Bioconductor + Quarto (mamba)
├── pyproject.toml                 # installs the `geo` CLI (console script)
├── geo_portfolio/                 # Python CLI / orchestration layer (no analysis logic)
│   └── cli.py  fetch.py  parse.py  suitability.py  report.py  scaffold.py  runner.py
├── tests/                         # CLI + triage unit tests (+ live tests, marked)
├── examples/                      # accessions.txt + sample triage reports (geo batch)
├── scripts/
│   ├── geo_helpers.R              # reusable analysis engine (incl. the data-type gate)
│   ├── build_triage.R             # aggregate suitability records -> TRIAGE.md
│   └── new_project.R              # scaffold a project from the template
├── templates/project_template/    # SUITABILITY.md + analysis.qmd + skeleton
└── projects/                      # one folder per dataset (GSE157830, GSE60450,
    └── GSE157830/                 #                        GSE78220, GSE2034)
        ├── SUITABILITY.md         # the triage report (decision gate)
        ├── README.md              # question, methods, results, interpretation, limits
        ├── analysis.qmd           # reproducible DE report
        ├── data/  results/{figures,tables}/  notes/
```

## Quick start

```bash
# Build the pinned environment once.
make env && mamba activate geo-rnaseq

# Triage a dataset: scaffold, then fill its SUITABILITY.md from the GEO record.
make new ACC=GSE123456 ORG=org.Hs.eg.db

# Regenerate the cross-dataset triage table from all suitability records.
make triage

# Analyze only datasets whose decision is "include".
make render PROJ=GSE123456
```

Prefer a single terminal command per step? The **`geo` CLI below** does triage,
scaffolding, and running without the Makefile.

## Getting the data from GEO

There are two kinds of GEO data, fetched at different stages:

**1. Metadata (SOFT)** — fetched automatically, no manual step.
- `geo triage` / `geo init-project` download series + sample metadata into `.geo_cache/`.
- Each `analysis.qmd` also pulls the verbatim sample metadata via `GEOquery::getGEO()`.

**2. Raw count matrices** — downloaded per project. These live in
`projects/<ACC>/data/raw/`, which is **gitignored** (large and reproducible), so
a fresh clone starts empty. Fetch the counts *before* `make render` / `geo run`.
The `geo` CLI is **triage-only** and does not download count matrices.

```bash
# GSE157830 / GSE60450 — counts are in the GEO supplementary files:
mkdir -p projects/GSE157830/data/raw
curl -L -o projects/GSE157830/data/raw/GSE157830_genes.counts.txt.gz \
  https://ftp.ncbi.nlm.nih.gov/geo/series/GSE157nnn/GSE157830/suppl/GSE157830_genes.counts.txt.gz

# GSE78220 — GEO has FPKM only, so raw counts come from recount3:
Rscript projects/GSE78220/scripts/prep_metadata.R
Rscript projects/GSE78220/scripts/prep_counts.R

# Generic — download ALL supplementary files of any series (language-agnostic):
Rscript -e 'GEOquery::getGEOSuppFiles("GSE123456", baseDir="projects/GSE123456/data/raw")'
```

The GEO FTP path follows the pattern
`…/geo/series/GSE<nnn>nnn/GSE<full>/suppl/<file>` where `GSE<nnn>nnn` truncates
the last three digits (e.g. `GSE157830` → `GSE157nnn`). Each project's README
lists the exact download command for that dataset.

## Command-line interface: `geo`

A Python CLI (`geo_portfolio`) wraps the same workflow for the terminal. It is an
**orchestration layer only** — it triages accessions, writes reports in the
existing `SUITABILITY.md` schema, scaffolds from the existing template, and calls
the existing R/Quarto analysis. It does **not** reimplement any analysis. Full
reference: [`docs/cli.md`](docs/cli.md).

### Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .            # console script is exactly: geo
geo --help
```

### One command end-to-end

```bash
geo pipeline GSE157830        # triage → scaffold → download counts → run, in one go
```

`pipeline` collapses the whole flow into a single command, but stays
conservative: it stops at the gate for `exclude`, never overwrites a curated
project without `--force`, auto-downloads the detected raw-count file, and only
auto-runs DESeq2 when `analysis.qmd` has actually been curated (otherwise it
prints the curation steps). For an already-curated dataset it is a true one-shot
reproduce.

### Or the individual commands

```bash
geo triage GSE157830                                            # decide, print summary
geo triage GSE157830 --out examples/reports/GSE157830 --format markdown,json
geo batch examples/accessions.txt --out examples/reports        # many at once + summary
geo data GSE157830                                              # download the count matrix
geo init-project GSE123456 --with-triage-report                 # scaffold a NEW dataset
geo run GSE157830 --project projects/GSE157830                  # gated on triage = include
```

(`scaffold`/`init-project`/`pipeline` refuse to overwrite an existing project
without `--force`, so the new-dataset example uses a fresh accession.)

### Example output

```
╭───────────────── SUITABLE · score 100/100 ─────────────────╮
│  accession  GSE157830                                       │
│      assay  bulk RNA-seq                                    │
│ raw counts  yes                                             │
│     design  ~ genotype                                      │
│  DE method  DESeq2                                          │
│   decision  include                                         │
╰──────────────────────── GSE157830 ─────────────────────────╯
```

Batch triage of the four portfolio datasets reproduces the curated decisions:

| accession | assay | raw counts | class | decision |
|-----------|-------|-----------|-------|----------|
| GSE157830 | bulk RNA-seq | yes | suitable | **include** |
| GSE60450 | bulk RNA-seq | yes | suitable | **include** |
| GSE78220 | bulk RNA-seq | no (FPKM only) | manual_review | **conditional** |
| GSE2034 | microarray | no | unsuitable | **exclude** |

### How `geo` connects to the existing workflow

The triage markdown uses the **same YAML front-matter** as the hand-written
`projects/*/SUITABILITY.md`, so `scripts/build_triage.R` aggregates CLI output
into `docs/TRIAGE.md` unchanged. `geo scaffold` copies
`templates/project_template/`; `geo run` calls `mamba run -n geo-rnaseq quarto
render`. Recommended loop:

```bash
geo triage GSE123456 --out examples/reports/GSE123456    # decide
geo init-project GSE123456 --with-triage-report          # scaffold (include/conditional)
Rscript scripts/build_triage.R                           # refresh docs/TRIAGE.md
geo run GSE123456                                        # analyze (include only)
```

### Limitations

- Triage is **metadata-only** — it does not inspect count *values* (e.g. it can't
  see RSEM fractional counts; the R `run_deseq2()` guard catches that at analysis time).
- Factor inference is heuristic — review reports before scaffolding.
- `geo run` needs the `geo-rnaseq` mamba environment.

### Conservative by design

Never claims DESeq2 compatibility without a detected raw **count** file; never
treats FPKM/TPM/RPKM as DESeq2 input; never infers groups from vague titles
(only `characteristics` fields; ambiguous ones are flagged); when uncertain →
**manual review**.

## What "demonstrates judgment" means here concretely

- The suitability report can return **exclude** (normalized-only data, no
  replicates, confounded design, wrong assay) — saying *no* with a reason is a
  first-class outcome, not a failure.
- The analysis engine **refuses** to run DESeq2 on non-integer/normalized values
  (`run_deseq2()` stops; `assess_data_type()` classifies first).
- Group labels are read from GEO `characteristics` fields, **never guessed** from
  sample titles; cleaning steps and assumptions are logged.

See [`docs/README.md`](docs/README.md) for the full methodology.

## Projects

See **[`docs/TRIAGE.md`](docs/TRIAGE.md)** for the live table. Current datasets:

| Dataset | Organism | Question | Decision | Why |
|---------|----------|----------|----------|-----|
| [GSE157830](projects/GSE157830/) | *H. sapiens* | GOT1 knockdown vs control in PDAC | **include** ✓ rendered | gene-level raw counts; 933 DEGs, GOT1 top hit |
| [GSE60450](projects/GSE60450/) | *M. musculus* | luminal vs basal mammary cells across stages | **include** ✓ rendered | raw count matrix; 7,347 DEGs, markers validate labels |
| [GSE334534](projects/GSE334534/) | *H. sapiens* | IgG-positive vs IgG-negative PL45 cells | **include** ✓ rendered | RSEM counts; 437 DEGs — modest/confounded, honest caveats |
| [GSE78220](projects/GSE78220/) | *H. sapiens* | anti-PD-1 responders vs non-responders | **include** ✓ promoted | FPKM-only on GEO → **promoted** with recount3 counts; 415 DEGs (IPRES signature) |
| [GSE2034](projects/GSE2034/) | *H. sapiens* | breast-cancer metastasis vs relapse-free | **exclude** | **microarray**, not RNA-seq — wrong assay for DESeq2 |

Three analyzed (one **promoted** from conditional by sourcing recount3 counts
instead of running DESeq2 on FPKM) and one **excluded** for wrong assay — the
spread is the point: triage that can say *yes*, *not yet → fixed*, and *no*.

## Disclaimer

Independent reanalyses of public data for portfolio and educational purposes;
not affiliated with or endorsed by the original data submitters.
