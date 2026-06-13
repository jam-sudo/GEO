---
# ── Machine-readable triage record ───────────────────────────────────────────
# Parsed by scripts/build_triage.R to build the cross-dataset comparison table.
# Every field is a deliberate judgment, not a default. Keep it honest.
accession: GSE60450
title: ""
organism: ""
assay_type: ""                 # bulk RNA-seq | scRNA-seq | microarray | other
platform: ""                   # GPL id + instrument
n_samples: 0
processed_files: []            # list of {name, type}; type ∈ raw_counts|fpkm|tpm|normalized_matrix|other
raw_counts_available: "unknown"  # "yes" | "no" | "unknown"  (quote — bare yes/no parse as booleans)
normalized_values_present: "unknown"   # "yes" | "no"  (TPM/FPKM/normalized matrix)
groups: []                     # list of {name, n_replicates}
min_replicates_per_group: 0
metadata_clarity: ""           # clear | moderate | messy
possible_contrasts: []         # list of strings
recommended_design: ""         # e.g. "~ batch + condition"  (NA if excluded)
de_method: ""                  # DESeq2 | edgeR | limma-voom | limma | none
decision: ""                   # include | conditional | exclude
decision_reasons: []           # list of strings — WHY include/exclude
# ─────────────────────────────────────────────────────────────────────────────
---

# Dataset suitability report — GSE60450

> Written **before** any differential-expression analysis. The point of this
> document is judgment: decide whether — and how — this public dataset can be
> reanalyzed, and justify it. DE is run only if `decision: include`.

## 1. Identity

| Field | Value |
|-------|-------|
| Accession | GSE60450 |
| Title | *fill* |
| Organism | *fill* |
| Assay type | *fill* |
| Platform | *fill* |
| # Samples | *fill* |

## 2. Available processed files

| File | Type | Use for DE? |
|------|------|-------------|
| *fill* | raw_counts / tpm / fpkm / normalized_matrix / other | *yes/no* |

- **Raw counts available?** *yes / no* — *evidence*
- **TPM / FPKM / normalized values present?** *yes / no* — *which*

## 3. Replication & groups

| Group | n replicates |
|-------|--------------|
| *fill* | *n* |

- **Minimum replicates per group:** *n* (DE needs ≥ 2, ideally ≥ 3).

## 4. Metadata clarity

*clear / moderate / messy* — *how groups are encoded (which characteristics
field), and any cleaning/assumptions required. Group labels come from
`characteristics_ch1.*`, never from free-text titles.*

## 5. Possible contrasts

- *fill — enumerate the biologically meaningful comparisons the design supports.*

## 6. Recommended statistical design

- **Method:** *DESeq2 (raw counts) / limma (normalized or microarray) / none.*
- **Design formula:** `~ ...` *(explicit; include batch/covariates if supported).*
- **Reference levels / primary contrast:** *fill.*

## 7. Decision — include / conditional / exclude

**Decision:** *fill.*

**Reasons:**

- *fill — the concrete reasons to include or exclude. Excluding for a good
  reason (normalized-only, no replicates, confounded design, wrong assay) is a
  valid and valuable outcome of triage.*
