---
accession: GSE60450
title: "Transcriptome analysis of luminal and basal cell subpopulations in the lactating versus pregnant mammary gland"
organism: "Mus musculus"
assay_type: "bulk RNA-seq"
platform: "GPL13112 (Illumina HiSeq 2000)"
n_samples: 12
processed_files:
  - {name: "GSE60450_Lactation-GenewiseCounts.txt.gz", type: raw_counts}
  - {name: "GSE60450_RAW.tar", type: other}
raw_counts_available: "yes"
normalized_values_present: "no"
groups:
  - {name: "basal_virgin", n_replicates: 2}
  - {name: "basal_pregnant", n_replicates: 2}
  - {name: "basal_lactating", n_replicates: 2}
  - {name: "luminal_virgin", n_replicates: 2}
  - {name: "luminal_pregnant", n_replicates: 2}
  - {name: "luminal_lactating", n_replicates: 2}
min_replicates_per_group: 2
metadata_clarity: clear
possible_contrasts:
  - "cell type: luminal vs basal (adjusted for stage) — well powered (n=6 vs 6)"
  - "developmental stage: lactating vs pregnant (within a cell type)"
  - "interaction: does the stage effect differ between luminal and basal cells"
recommended_design: "~ cell_type + stage"
de_method: DESeq2
decision: include
decision_reasons:
  - "Gene-wise raw count matrix deposited (GSE60450_Lactation-GenewiseCounts.txt.gz) — DESeq2/edgeR valid."
  - "Clean 2x3 factorial design (cell type x developmental stage)."
  - "Caveat: only 2 replicates per finest group — adequate but low-powered for the 6-group split."
---

# Dataset suitability report — GSE60450

> Verdict: **INCLUDE** (queued; analysis not yet run). A second mouse RNA-seq
> dataset chosen to broaden the portfolio beyond a single human study and to
> exercise a factorial design.

## 1. Identity

| Field | Value |
|-------|-------|
| Accession | GSE60450 |
| Title | *Transcriptome analysis of luminal and basal cell subpopulations in the lactating versus pregnant mammary gland* |
| Organism | *Mus musculus* (→ `org.Mm.eg.db`) |
| Assay type | Bulk RNA-seq |
| Platform | GPL13112 — Illumina HiSeq 2000 |
| # Samples | 12 (2 cell types × 3 stages × 2 mice) |

## 2. Available processed files

| File | Type | Use for DE? |
|------|------|-------------|
| `GSE60450_Lactation-GenewiseCounts.txt.gz` | **gene-wise raw counts** | **YES** |
| `GSE60450_RAW.tar` | per-sample raw files | Not needed |

- **Raw counts available?** **Yes** — a single gene-wise count matrix.
- **TPM/FPKM/normalized present?** No normalized supplementary matrix.

## 3. Replication & groups

Six groups (luminal/basal × virgin/pregnant/lactating), **2 replicates each**.
A cell-type contrast pools to n = 6 per side (well powered); the finest
stage-within-cell-type contrasts rest on n = 2 (usable but low power).

## 4. Metadata clarity

**Clear** at the series level (factors = cell type, developmental stage). *To
hold the framework's standard, the per-sample `characteristics_ch1.*` fields
must be confirmed at analysis time before assigning groups — not yet pulled, as
this entry is triage-only.*

## 5. Possible contrasts

- **Luminal vs basal**, adjusting for stage (primary, well powered).
- Lactating vs pregnant within a cell type.
- Cell-type × stage interaction (whether the stage response differs by lineage).

## 6. Recommended statistical design

- **Method:** DESeq2 (or edgeR / limma-voom) on the raw count matrix.
- **Design formula:** `~ cell_type + stage` (add interaction `cell_type:stage`
  to test lineage-specific stage effects).

## 7. Decision — INCLUDE

**Decision:** **include** (analysis queued).

**Reasons:** raw gene counts deposited; clean factorial design; only caveat is
the modest 2-replicate-per-group depth, noted as a limitation rather than a
disqualifier.
