---
accession: GSE157830
title: "Labile Iron Release Primes Pancreatic Cancer for Ferroptosis"
organism: "Homo sapiens"
assay_type: "bulk RNA-seq"
platform: "GPL24676 (Illumina NovaSeq 6000)"
n_samples: 12
processed_files:
  - {name: "GSE157830_genes.counts.txt.gz", type: raw_counts}
  - {name: "GSE157830_genes.FPKM.txt.gz", type: fpkm}
  - {name: "GSE157830_genes.TPM.txt.gz", type: tpm}
  - {name: "GSE157830_isoforms.counts.txt.gz", type: raw_counts}
  - {name: "GSE157830_isoforms.FPKM.txt.gz", type: fpkm}
  - {name: "GSE157830_isoforms.TPM.txt.gz", type: tpm}
raw_counts_available: "yes"
normalized_values_present: "yes"
groups:
  - {name: "Tu8902_control", n_replicates: 3}
  - {name: "Tu8902_GOT1_knockdown", n_replicates: 3}
  - {name: "MiaPaCa2_control", n_replicates: 3}
  - {name: "MiaPaCa2_GOT1_knockdown", n_replicates: 3}
min_replicates_per_group: 3
metadata_clarity: clear
possible_contrasts:
  - "GOT1_knockdown vs control (adjusted for cell line) — PRIMARY"
  - "GOT1_knockdown vs control within Tu8902 only"
  - "GOT1_knockdown vs control within MiaPaCa2 only"
  - "cell line: MiaPaCa2 vs Tu8902 (baseline difference; not the question)"
recommended_design: "~ cell_line + treatment"
de_method: DESeq2
decision: include
decision_reasons:
  - "Gene-level raw (RSEM) counts available — DESeq2 is statistically valid."
  - "Balanced 2x2 design, 3 replicates per group."
  - "Group labels unambiguous (characteristics genotype/variation) and biologically confirmed (GOT1 counts collapse ~20-30x in knockdown)."
---

# Dataset suitability report — GSE157830

> Written before any differential-expression analysis. Verdict: **INCLUDE** —
> reanalyze with DESeq2, design `~ cell_line + treatment`.

## 1. Identity

| Field | Value |
|-------|-------|
| Accession | GSE157830 |
| Title | *Labile Iron Release Primes Pancreatic Cancer for Ferroptosis* |
| Organism | *Homo sapiens* |
| Assay type | Bulk RNA-seq (polyA) |
| Platform | GPL24676 — Illumina NovaSeq 6000 |
| # Samples | 12 (2 cell lines × 2 treatments × 3 replicates) |
| BioProject / SRA | PRJNA662926 / SRP282058 |

## 2. Available processed files

| File | Type | Use for DE? |
|------|------|-------------|
| `GSE157830_genes.counts.txt.gz` | **gene-level RSEM raw counts** | **YES** (after rounding) |
| `GSE157830_genes.FPKM.txt.gz` | gene FPKM (normalized) | No |
| `GSE157830_genes.TPM.txt.gz` | gene TPM (normalized) | No |
| `GSE157830_isoforms.{counts,FPKM,TPM}.txt.gz` | isoform-level | No (gene-level DE) |
| `GSE157830_RAW.tar` | per-sample raw files | Not needed |

- **Raw counts available?** **Yes** — `GSE157830_genes.counts.txt.gz`, 8
  annotation columns + 12 sample columns, 58,721 genes (verified by direct
  inspection). Values are **RSEM expected counts** (fractional, e.g. `ACTB` =
  210040.69) → must be **rounded** for DESeq2; FPKM/TPM are excluded.
- **TPM / FPKM / normalized values present?** Yes (FPKM and TPM files) — not used
  for DE.

## 3. Replication & groups

| Group | n replicates |
|-------|--------------|
| Tu8902 control (−Dox) | 3 |
| Tu8902 GOT1 knockdown (+Dox) | 3 |
| MiaPaCa2 control (−Dox) | 3 |
| MiaPaCa2 GOT1 knockdown (+Dox) | 3 |

- **Minimum replicates per group:** 3 — adequate for DESeq2.

## 4. Metadata clarity

**Clear.** Groups are encoded in the GEO `genotype/variation` characteristics
field (`control` / `GOT1 knockdown`), not inferred from titles. The sample-name
token `mnsdox`/`plsdox` (minus/plus doxycycline) and the GOT1 read counts
independently corroborate the assignment. Cleaning required: map `Mia` →
MiaPaCa2 (source_name), round RSEM counts, de-duplicate ~45 non-unique Ensembl
IDs. All decisions are logged in the project README and `analysis.qmd`.

## 5. Possible contrasts

- **GOT1 knockdown vs control, adjusted for cell line** — *primary* (the question).
- GOT1 knockdown vs control within Tu8902 only.
- GOT1 knockdown vs control within MiaPaCa2 only.
- MiaPaCa2 vs Tu8902 baseline (a nuisance axis, not the biological question).

## 6. Recommended statistical design

- **Method:** DESeq2 on rounded gene-level counts.
- **Design formula:** `~ cell_line + treatment` (adjusts for the cell-line
  baseline, estimates the shared GOT1-knockdown effect; additive, no interaction).
- **Reference levels:** `treatment = control`, `cell_line = Tu8902`.
- **Primary contrast:** `treatment`: GOT1_knockdown vs control.

## 7. Decision — INCLUDE

**Decision:** **include.**

**Reasons:**

- Gene-level **raw counts are available**, so DESeq2 is statistically appropriate.
- **Balanced** 2×2 design with **3 replicates per group**.
- **Unambiguous, confirmed** group labels (characteristics field + biological
  positive control via GOT1 knockdown magnitude).
- Only routine, well-documented cleaning needed (round RSEM counts, de-dup IDs).
