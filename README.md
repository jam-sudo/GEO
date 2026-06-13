# GEO RNA-seq Differential Expression Portfolio

A portfolio of reproducible RNA-seq differential-expression re-analyses of
public [GEO](https://www.ncbi.nlm.nih.gov/geo/) datasets. Each project starts
from a clear biological question, downloads real GEO metadata (never invented),
determines whether the data are suitable for standard differential expression,
and produces publication-quality figures with a concise biological
interpretation.

> **Author:** jam-sudo

## Why this repo is structured the way it is

GEO datasets are inconsistent — some provide raw counts, some only normalized
values, some are microarray. A core principle here is **honesty about the
data**: before running DESeq2, every project runs a *decision gate* that
classifies the data type and refuses to treat normalized values as raw counts.
See [`docs/README.md`](docs/README.md) for the full methodology.

## Repository structure

```
geo-rnaseq-portfolio/
├── README.md                # you are here
├── Makefile                 # make env / new / render / render-all
├── environment/             # mamba environment.yml (R + Bioconductor + Quarto)
├── scripts/
│   ├── geo_helpers.R        # reusable analysis functions (the engine)
│   └── new_project.R        # scaffold a project from the template
├── templates/
│   └── project_template/    # copyable per-dataset skeleton (qmd + README + dirs)
├── projects/
│   └── GSEXXXXXX/           # one folder per dataset
│       ├── README.md        # question, samples, results, limitations
│       ├── analysis.qmd     # the reproducible report
│       ├── data/            # downloaded GEO data (raw files gitignored)
│       ├── results/
│       │   ├── figures/     # publication-quality plots (tracked)
│       │   └── tables/      # DE + enrichment tables (tracked)
│       ├── scripts/         # dataset-specific code, if any
│       └── notes/           # working notes / decisions
└── docs/                    # methodology & conventions
```

## Quick start

```bash
# 1. Build the environment once (R, Bioconductor, Quarto).
make env
mamba activate geo-rnaseq

# 2. Scaffold a dataset and render it (first render downloads data + prints
#    the data-type verdict).
make new ACC=GSE123456 ORG=org.Hs.eg.db
make render PROJ=GSE123456
```

Then open `projects/GSE123456/analysis.qmd`, fill the biological question, set
the count-loading chunk, and choose `params$group_col` / `params$contrast`.

## What each project delivers

- **Documented provenance** — GEO accession + sample metadata saved verbatim.
- **Data-type verdict** — raw counts vs normalized-only vs unsuitable, stated up front.
- **QC** — library sizes, count distribution, PCA, sample-correlation heatmap.
- **Differential expression** (when valid) — results table (gene ID, symbol,
  log2FC, p-value, adjusted p-value), volcano plot, MA plot, top-gene heatmap.
- **Functional interpretation** — GO/pathway enrichment + a written summary.
- **Limitations** — an honest, dataset-specific caveats section.

## Reproducibility

One mamba environment pins the whole toolchain; every report embeds
`sessionInfo()`; any analysis re-runs with a single `make render`. See
[`environment/environment.yml`](environment/environment.yml).

## Projects

| Dataset | Organism | Question | Data type | Status |
|---------|----------|----------|-----------|--------|
| [GSE157830](projects/GSE157830/) | *H. sapiens* | GOT1 knockdown vs control in PDAC (Tu8902, MiaPaCa2) | Gene-level RSEM raw counts | Suitability ✓, analysis coded; renders once env is built |

<!-- Add a row per dataset as projects are completed. -->

## Disclaimer

These are independent re-analyses of public data for portfolio and educational
purposes; they are not affiliated with or endorsed by the original data
submitters.
