---
accession: GSE2034
title: "Breast cancer relapse free survival"
organism: "Homo sapiens"
assay_type: "microarray"
platform: "GPL96 (Affymetrix HG-U133A)"
n_samples: 286
processed_files:
  - {name: "GSE2034 series matrix", type: normalized_matrix}
  - {name: "GSE2034_RAW.tar (Affymetrix CEL files)", type: other}
raw_counts_available: "no"
normalized_values_present: "yes"
groups:
  - {name: "relapse_free", n_replicates: 180}
  - {name: "distant_metastasis", n_replicates: 106}
min_replicates_per_group: 106
metadata_clarity: moderate
possible_contrasts:
  - "distant metastasis vs relapse-free (microarray DE via limma)"
recommended_design: "~ outcome  (limma on log2 intensities — NOT a count model)"
de_method: "limma (microarray); DESeq2/edgeR not applicable"
decision: exclude
decision_reasons:
  - "Affymetrix microarray, not RNA-seq — there are no sequencing counts, so the count-based DESeq2 framework does not apply."
  - "Out of scope for this RNA-seq reanalysis portfolio; the correct tool would be limma on normalized intensities."
---

# Dataset suitability report — GSE2034

> Verdict: **EXCLUDE** from this RNA-seq reanalysis framework — *wrong assay*, not
> bad data. Included in triage to demonstrate assay-type screening: the framework
> recognizes when DESeq2 is categorically inapplicable.

## 1. Identity

| Field | Value |
|-------|-------|
| Accession | GSE2034 |
| Title | *Breast cancer relapse free survival* |
| Organism | *Homo sapiens* |
| Assay type | **Microarray** (Affymetrix 3'-IVT) |
| Platform | GPL96 — Affymetrix Human Genome U133A |
| # Samples | 286 |

## 2. Available processed files

| File | Type | Use for DE? |
|------|------|-------------|
| Series matrix | normalized Affymetrix intensities | not for DESeq2 |
| `GSE2034_RAW.tar` | Affymetrix CEL files | microarray, not counts |

- **Raw counts available?** **No** — there is no sequencing-count concept here;
  the rawest form is CEL intensity files.
- **TPM/FPKM/normalized present?** Yes — normalized microarray intensities.

## 3. Replication & groups

Large cohort: 180 relapse-free vs 106 distant-metastasis tumors. Replication is
abundant — this is purely an **assay-type** exclusion, not a power problem.

## 4. Metadata clarity

**Moderate.** Outcome (relapse) and clinical covariates are provided; mapping is
feasible.

## 5. Possible contrasts

- Distant metastasis vs relapse-free — a valid biological question, but one to be
  answered with microarray-appropriate methods.

## 6. Recommended statistical design

- **DESeq2/edgeR: not applicable** — these model integer sequencing counts with a
  negative-binomial mean–variance relationship that microarray intensities do not
  follow.
- **Correct tool:** `limma` on log2-normalized intensities, `~ outcome`.

## 7. Decision — EXCLUDE

**Decision:** **exclude** (from this RNA-seq, count-based framework).

**Reasons:** it is a microarray dataset with no sequencing counts; forcing it
into a DESeq2 pipeline would be a category error. The right analysis (limma on
intensities) is out of scope for an RNA-seq reanalysis portfolio. Screening this
out is the point — knowing which tool a dataset calls for is part of the
judgment being demonstrated.
