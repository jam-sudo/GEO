---
accession: GSE78220
title: "mRNA expressions in pre-treatment melanomas undergoing anti-PD-1 checkpoint inhibition therapy"
organism: "Homo sapiens"
assay_type: "bulk RNA-seq"
platform: "GPL11154 (Illumina HiSeq 2000)"
n_samples: 28
processed_files:
  - {name: "GSE78220_PatientFPKM.xlsx", type: fpkm}
raw_counts_available: "no"
normalized_values_present: "yes"
groups:
  - {name: "responder", n_replicates: null}
  - {name: "non_responder", n_replicates: null}
min_replicates_per_group: null
metadata_clarity: moderate
possible_contrasts:
  - "anti-PD-1 responder vs non-responder"
recommended_design: "~ response  (valid ONLY on raw counts re-derived from SRA/recount3)"
de_method: "DESeq2 (requires raw counts; FPKM as deposited is not valid input)"
decision: conditional
decision_reasons:
  - "RNA-seq, but the ONLY deposited expression file is FPKM (GSE78220_PatientFPKM.xlsx) — DESeq2/edgeR must not be run on FPKM."
  - "Raw counts are recoverable: reprocess SRA SRP070710, or pull precomputed counts from recount3/ARCHS4 — then this becomes INCLUDE."
---

# Dataset suitability report — GSE78220

> Verdict: **CONDITIONAL** — a genuine RNA-seq study with a strong biological
> question, but the data **as deposited** cannot go into DESeq2. This is exactly
> the trap the framework exists to catch.

## 1. Identity

| Field | Value |
|-------|-------|
| Accession | GSE78220 |
| Title | *mRNA expressions in pre-treatment melanomas undergoing anti-PD-1 checkpoint inhibition therapy* |
| Organism | *Homo sapiens* |
| Assay type | Bulk RNA-seq (paired-end) |
| Platform | GPL11154 — Illumina HiSeq 2000 |
| # Samples | 28 |
| SRA | SRP070710 |

## 2. Available processed files

| File | Type | Use for DE? |
|------|------|-------------|
| `GSE78220_PatientFPKM.xlsx` | **FPKM (normalized)** | **NO** |

- **Raw counts available?** **No** — no count matrix is deposited.
- **TPM/FPKM/normalized present?** Yes — **FPKM only**, in an Excel file.

## 3. Replication & groups

28 tumors split into anti-PD-1 **responders vs non-responders** — replication is
ample and is *not* the limiting factor here. (Exact per-group counts to be
confirmed from the metadata at analysis time.)

## 4. Metadata clarity

**Moderate.** Response status must be mapped from the clinical annotation onto
the FPKM matrix columns; straightforward but requires care.

## 5. Possible contrasts

- **Responder vs non-responder** (the biological question).

## 6. Recommended statistical design

- **As deposited:** none valid for count-based DE — **FPKM must not enter
  DESeq2/edgeR** (per-gene cross-sample comparisons on FPKM are statistically
  unsound).
- **Correct path:** obtain raw counts by reprocessing **SRA SRP070710** (or pull
  precomputed counts from **recount3 / ARCHS4**), then DESeq2 with `~ response`.
- A limma-trend analysis on `log2(FPKM+1)` is a weaker fallback and would be
  clearly labelled as such, not presented as a count-based DESeq2 result.

## 7. Decision — CONDITIONAL

**Decision:** **conditional** — promote to *include* only after raw counts are
obtained from SRA/recount3.

**Reasons:** the deposited FPKM cannot support a valid DESeq2 analysis, but the
underlying reads exist publicly, so the dataset is rescuable rather than a hard
exclude. Documenting this — instead of silently running DESeq2 on FPKM — is the
judgment the portfolio is meant to show.
