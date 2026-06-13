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
├── docs/
│   ├── TRIAGE.md                  # cross-dataset comparison (the headline)
│   ├── triage.csv                 # machine-readable triage table
│   └── README.md                  # methodology & conventions
├── Makefile                       # make triage / env / new / render
├── environment/environment.yml    # pinned R + Bioconductor + Quarto (mamba)
├── scripts/
│   ├── geo_helpers.R              # reusable analysis engine (incl. the data-type gate)
│   ├── build_triage.R             # aggregate suitability records -> TRIAGE.md
│   └── new_project.R              # scaffold a project from the template
├── templates/project_template/    # SUITABILITY.md + analysis.qmd + skeleton
└── projects/
    └── GSE157830/
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
| [GSE78220](projects/GSE78220/) | *H. sapiens* | anti-PD-1 responders vs non-responders | **conditional** | RNA-seq but **FPKM-only**; needs SRA/recount3 counts |
| [GSE2034](projects/GSE2034/) | *H. sapiens* | breast-cancer metastasis vs relapse-free | **exclude** | **microarray**, not RNA-seq — wrong assay for DESeq2 |

Two `include`d, one `conditional` (rescuable from SRA), one `exclude`d (wrong
assay) — the spread is the point: triage that can say *no* and *not yet*, not
just *yes*.

## Disclaimer

Independent reanalyses of public data for portfolio and educational purposes;
not affiliated with or endorsed by the original data submitters.
