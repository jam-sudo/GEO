# Dataset suitability review — GSEXXXXXX

> Complete this BEFORE writing any analysis code. The goal is to decide whether
> — and how — this dataset can be analyzed for differential expression, based on
> what GEO actually provides. No DESeq2 on normalized values. No guessing group
> labels from titles — read the `characteristics_ch1.*` fields.

## 1. Dataset identity

| Field | Value | Source |
|-------|-------|--------|
| Accession | GSEXXXXXX | GEO |
| Title | *fill* | GEO series record |
| Organism | *fill* | series / sample |
| Assay type | *RNA-seq / microarray / scRNA-seq / other* | series summary + platform |
| Platform (GPL) | *fill* (e.g. GPL24676 Illumina NovaSeq) | GEO |
| # Samples | *fill* | GEO |
| Design summary | *e.g. 3 control vs 3 treated, paired?* | characteristics fields |

## 2. Available files

| File | Type | Looks like | Notes |
|------|------|-----------|-------|
| `GSEXXXXXX_series_matrix.txt.gz` | series matrix | metadata (+ maybe values) | always present |
| *supp file 1* | supplementary | *raw counts / TPM / FPKM / ?* | inspect header + value range |
| *supp file 2* | supplementary | | |

## 3. Data-type determination

- **Values inspected:** *integer vs continuous; value range; presence of decimals.*
- **Verdict:** `raw_counts` / `tpm` / `fpkm` / `normalized_matrix` / `microarray` / `other`
- **Evidence:** *why — e.g. "supp file `*_raw_counts.tsv.gz` has integer values 0–48,213".*

## 4. Appropriate DE method

| If data are... | Use | Not |
|----------------|-----|-----|
| Raw integer counts | **DESeq2** (or edgeR/limma-voom) with explicit design | — |
| TPM / FPKM only | limma-trend on log2(x+1), **clearly labelled**; or refetch raw counts (recount3/ARCHS4/SRA) | DESeq2 |
| Normalized microarray (RMA/quantile) | **limma** on log2 intensities | DESeq2, edgeR |
| Single-cell | pseudobulk → DESeq2, or scran/scvi | bulk DESeq2 on cells |

- **Chosen method + justification:** *fill*
- **Explicit design formula:** `~ <covariate(s)> + <group>` *fill*

## 5. Conditions & cleaned metadata

Read `characteristics_ch1.*` (NOT the free-text title) to assign groups.

- **Grouping variable(s):** *fill — exact GEO field name(s)*
- **Group levels & n:** *fill*
- **Covariates / batch:** *fill or "none documented"*
- **Cleaned metadata table:** saved to `data/GSEXXXXXX_metadata_clean.csv`
  (raw metadata kept verbatim in `data/GSEXXXXXX_sample_metadata.csv`).

## 6. Assumptions log

Document every assumption made when cleaning messy metadata (one line each):

- *e.g. "Samples labelled 'siCtrl' mapped to control; confirmed via characteristics field `treatment: control siRNA`."*

## 7. Go / no-go decision

- [ ] **GO** — suitable for the standard DE workflow as scoped above.
- [ ] **CONDITIONAL** — proceed with a non-DESeq2 method / documented limitation.
- [ ] **NO-GO** — not suitable for standard RNA-seq DE. Reason: *fill*.

**Decision:** *fill* — *one-sentence rationale.*
