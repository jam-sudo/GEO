---
accession: GSE78220
title: "mRNA expressions in pre-treatment melanomas undergoing anti-PD-1 checkpoint inhibition therapy"
organism: "Homo sapiens"
assay_type: "bulk RNA-seq"
platform: "GPL11154 (Illumina HiSeq 2000)"
n_samples: 28
processed_files:
  - {name: "GSE78220_PatientFPKM.xlsx", type: fpkm}
  - {name: "recount3 SRP070710 (gene_sums)", type: raw_counts}
raw_counts_available: "recount3"
normalized_values_present: "yes"
groups:
  - {name: "responder (CR/PR)", n_replicates: 15}
  - {name: "non_responder (PD)", n_replicates: 13}
min_replicates_per_group: 13
metadata_clarity: moderate
possible_contrasts:
  - "anti-PD-1 responder (CR/PR) vs non-responder (PD)"
recommended_design: "~ response"
de_method: "DESeq2 (recount3 counts)"
decision: include
promoted_from: conditional
decision_reasons:
  - "PROMOTED from conditional: GEO deposits only FPKM, but raw gene counts were obtained from recount3 (SRP070710), making DESeq2 valid."
  - "Balanced cohort: 15 responders (CR/PR) vs 13 non-responders (PD), no ambiguous stable-disease cases."
---

# Dataset suitability report — GSE78220

> Verdict: **INCLUDE (promoted from CONDITIONAL).** As deposited on GEO this
> dataset is FPKM-only and could not enter DESeq2; we promoted it by pulling raw
> counts from recount3. This conditional → include arc is the judgment the
> portfolio is built to show.

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
| `GSE78220_PatientFPKM.xlsx` (GEO) | FPKM (normalized) | **NO** |
| recount3 `SRP070710` gene_sums | **raw gene counts** | **YES** (used) |

- **Raw counts in the GEO deposit?** No. **Obtained from recount3** (uniform SRA
  reprocessing) — see [`scripts/prep_counts.R`](scripts/prep_counts.R).
- **Normalized values present?** Yes — FPKM, on GEO (not used).

## 3. Replication & groups

28 pre-treatment tumors → **15 responders** (Complete/Partial Response) vs
**13 non-responders** (Progressive Disease). Ample replication; the original
blocker was data type, not power.

## 4. Metadata clarity

**Moderate.** The GEO `characteristics_ch1.*` fields are **ragged** (the
`anti-pd-1 response` field sits at different column positions across samples), so
response was extracted by scanning all characteristics columns per sample (see
[`scripts/prep_metadata.R`](scripts/prep_metadata.R)). RECIST categories were
dichotomized: responder = CR/PR, non-responder = PD (no stable-disease cases).
SRA experiment accessions (SRX) were used to join GEO samples to recount3.

## 5. Possible contrasts

- **Responder vs non-responder** (the biological question).

## 6. Recommended statistical design

- **Method:** DESeq2 on recount3 raw counts, `~ response`
  (ref = non_responder, contrast responder vs non_responder).
- **Not valid:** DESeq2/edgeR on the deposited FPKM.

## 7. Decision — INCLUDE (promoted)

**Decision:** **include**, promoted from **conditional**.

**Reasons:** the deposited FPKM cannot support a valid count model, but the reads
are public; recount3 provides uniformly reprocessed raw counts, which we used.
The dataset went from "not yet — wrong data type as deposited" to a valid
analysis without ever running DESeq2 on FPKM.
