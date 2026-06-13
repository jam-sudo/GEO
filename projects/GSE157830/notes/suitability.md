# Dataset suitability review — GSE157830

> Completed BEFORE writing analysis code, from the GEO record and direct
> inspection of the supplementary count file. Verdict: **GO** — suitable for
> standard DESeq2 differential expression on raw gene-level counts.

## 1. Dataset identity

| Field | Value | Source |
|-------|-------|--------|
| Accession | GSE157830 | GEO |
| Title | *Labile Iron Release Primes Pancreatic Cancer for Ferroptosis* | series record |
| Organism | *Homo sapiens* | series / samples |
| Assay type | Bulk RNA-seq (polyA) | library strategy = RNA-Seq |
| Platform | GPL24676 — Illumina NovaSeq 6000 | GEO |
| # Samples | 12 (3 replicates × 2 treatments × 2 cell lines) | GEO |
| Design | GOT1 knockdown via dox-inducible shRNA in Tu8902 and MiaPaCa2 | overall design + characteristics |
| BioProject / SRA | PRJNA662926 / SRP282058 | GEO |

## 2. Available files

| File | Looks like | Use for DE? |
|------|-----------|-------------|
| `GSE157830_genes.counts.txt.gz` | **gene-level RSEM expected counts** | **YES** (after rounding) |
| `GSE157830_genes.FPKM.txt.gz` | gene FPKM (normalized) | No — normalized |
| `GSE157830_genes.TPM.txt.gz` | gene TPM (normalized) | No — normalized |
| `GSE157830_isoforms.{counts,FPKM,TPM}.txt.gz` | isoform-level | Not used (gene-level DE) |
| `GSE157830_RAW.tar` | per-sample raw files | Not needed (matrix provided) |

**Count-file structure (verified by direct inspection):** 8 annotation columns
(`gene_name`, `ensembl_gene_id`, `gene_type`, `entrez`, transcript fields,
`gene_description`) + 12 sample count columns; 58,721 gene rows.

## 3. Data-type determination

- **Verdict:** `raw_counts` (gene-level), **RSEM expected counts**.
- **Evidence:** values are non-negative and mostly integer, but a subset are
  fractional (e.g. `ACTB` = 210040.69, 210933.71; 37,609 of ~704k values carry a
  decimal point). Fractional values are the RSEM "expected_count" signature.
- **Consequence:** RSEM expected counts must be **rounded to integers** before
  DESeq2 (standard practice when not importing via `tximport`). The FPKM/TPM
  files are explicitly **excluded** from DE.

## 4. Appropriate DE method

- **Method:** DESeq2 on rounded gene-level counts. Balanced design (3 vs 3 per
  line), adequate for the negative-binomial model.
- **Design formula:** `~ cell_line + treatment` — controls for the large
  baseline expression difference between the two cell lines and estimates the
  shared GOT1-knockdown effect (an additive main-effect model, no interaction).
- **Reference levels:** `treatment` ref = `control`; `cell_line` ref = `Tu8902`.
- **Primary contrast:** `treatment`: `GOT1_knockdown` vs `control`
  (i.e. +Dox/plsdox vs −Dox/mnsdox).

## 5. Conditions & cleaned metadata

Groups are taken from the GEO `genotype/variation` **characteristics** field
(not parsed from the title); the `mnsdox`/`plsdox` token in the sample name and
the GOT1 read counts independently corroborate them.

| Token (sample name) | Meaning | Maps to treatment |
|---------------------|---------|-------------------|
| `mnsdox` | minus doxycycline (uninduced) | `control` |
| `plsdox` | plus doxycycline (shGOT1 induced) | `GOT1_knockdown` |

- **cell_line:** `Tu8902` (name prefix `Tu8902`) / `MiaPaCa2` (name prefix `Mia`,
  source_name = "MiaPaCa2").
- **treatment:** `control` (mnsdox) / `GOT1_knockdown` (plsdox).
- Cleaned table: `data/GSE157830_metadata_clean.csv` (raw metadata kept verbatim
  in `data/GSE157830_sample_metadata.csv` once downloaded via GEOquery).

## 6. Assumptions log

- **A1.** `mnsdox` = −Dox = control; `plsdox` = +Dox = GOT1 knockdown.
  *Confirmed three ways:* characteristics `genotype/variation` (control vs GOT1
  knockdown), the name token, and GOT1 counts collapsing ~20–30× in `plsdox`.
- **A2.** RSEM expected counts rounded to nearest integer for DESeq2.
- **A3.** `ensembl_gene_id` (versioned) used as unique rownames; `gene_name` is
  not unique (e.g. ATXN7, CCDC39 appear on multiple Ensembl IDs) so it is kept
  only as a label column. ~45 non-unique Ensembl IDs are made unique with
  `make.unique`.
- **A4.** Cell line `Mia` interpreted as **MiaPaCa2** (per sample source_name).
- **A5.** Control = uninduced (−Dox) shGOT1 cells; there is no separate
  non-targeting-shRNA +Dox arm, so a doxycycline-intrinsic effect cannot be
  fully excluded (see Limitations in the project README).

## 7. Go / no-go decision

- [x] **GO** — suitable for the standard DESeq2 workflow with design
  `~ cell_line + treatment`, contrast GOT1_knockdown vs control.

**Decision:** GO — gene-level raw (RSEM) counts are available and the 2×2
balanced design supports a cell-line-adjusted DESeq2 comparison; the only
data-specific handling required is rounding RSEM counts and de-duplicating IDs.
