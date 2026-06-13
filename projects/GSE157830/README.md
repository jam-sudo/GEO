# GSE157830 — GOT1 knockdown in pancreatic cancer (Tu8902 & MiaPaCa2)

> A reproducible re-analysis of RNA-seq data measuring how knocking down the
> metabolic enzyme **GOT1** changes gene expression in two pancreatic-cancer cell
> lines. In plain terms: we turn off one gene that pancreatic-cancer cells lean
> on, and read out which other genes and pathways shift in response.

## Biological question

Pancreatic ductal adenocarcinoma (PDAC) cells use **GOT1** (glutamic-oxaloacetic
transaminase 1) to balance their internal chemistry (redox state). The source
study (*"Labile Iron Release Primes Pancreatic Cancer for Ferroptosis"*) knocked
down GOT1 with a **doxycycline-inducible shRNA** and asked what happens
downstream. This project re-derives the differential-expression answer:

**Which genes and pathways respond to GOT1 knockdown, consistently across two
PDAC cell lines?**

## Dataset

| Field | Value |
|-------|-------|
| GEO accession | [GSE157830](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE157830) |
| Organism | *Homo sapiens* |
| Platform | GPL24676 — Illumina NovaSeq 6000 |
| Samples | 12: Tu8902 & MiaPaCa2 × control/knockdown × 3 replicates |
| Data type | **Gene-level RSEM raw counts** (rounded for DESeq2) |
| Design formula | `~ cell_line + treatment` |
| Primary contrast | GOT1 knockdown (+Dox/plsdox) vs control (−Dox/mnsdox) |
| BioProject / SRA | PRJNA662926 / SRP282058 |

Raw counts are downloaded from GEO; the **cleaned design table** is
[`data/GSE157830_metadata_clean.csv`](data/GSE157830_metadata_clean.csv).

## Suitability review (done before any analysis)

See [`SUITABILITY.md`](SUITABILITY.md) for the full triage report. Headlines:

- **Gene-level raw counts are available** (`GSE157830_genes.counts.txt.gz`) — DESeq2 is valid.
- Values are **RSEM expected counts** (fractional) → **rounded to integers** before DESeq2. FPKM/TPM files are *not* used.
- Group labels come from the GEO **`genotype/variation` characteristics field**, not the sample titles. Confirmed independently by the `mnsdox`/`plsdox` name token and by GOT1 read counts collapsing ~20–30× in the knockdown arm.

## Methods

DESeq2 on rounded gene-level counts, design `~ cell_line + treatment` (adjusts
for the cell-line baseline, estimates the shared knockdown effect), contrast
GOT1_knockdown vs control. Significance: `padj < 0.05` & `|log2FC| > 1`. PCA /
heatmaps use the variance-stabilizing transform; GO-BP over-representation via
clusterProfiler on the in-file Entrez IDs. Full code: [`analysis.qmd`](analysis.qmd).

## How to reproduce

```bash
mamba activate geo-rnaseq            # built from ../../environment/environment.yml
make render PROJ=GSE157830           # from the repo root -> analysis.html
```

## Results

Rendering produces these portfolio artifacts:

- **Figures** (`results/figures/`): `qc_library_sizes.png`,
  `qc_count_distribution.png`, `qc_pca.png` (treatment colour, cell-line shape),
  `qc_sample_correlation.png`, `volcano.png`, `ma_plot.png`,
  `top_genes_heatmap.png`, `go_bp_enrichment.png`.
- **Tables** (`results/tables/`): `GSE157830_DE_results.csv` (gene ID, symbol,
  log2FC, p, padj), `GSE157830_GO_BP_enrichment.csv`,
  `GSE157830_metadata_clean.csv`.

> Status: analysis code + suitability review complete and verified against the
> real count file (GOT1 positive-control confirmed). Figures/tables are generated
> on render once the `geo-rnaseq` environment is built. Interpretation below is
> filled in from the rendered results.

## Interpretation

*To be completed from the rendered results — top up/down genes, leading GO
terms, and how they relate to GOT1's role in aspartate/redox metabolism and the
study's ferroptosis theme.*

## Limitations

- **Control is uninduced (−Dox)**, not a non-targeting-shRNA +Dox arm, so a
  doxycycline-intrinsic effect cannot be fully separated from GOT1 knockdown.
- **RSEM counts were rounded** to meet DESeq2's integer requirement (a `tximport`
  workflow would handle estimation uncertainty more rigorously).
- **Additive model** estimates a shared effect only; testing cell-line-specific
  responses would require an interaction term (`~ cell_line * treatment`).
- Two cell lines, n = 3 each — findings describe these models, not PDAC broadly.

## Notes

Working notes and the suitability review are in [`notes/`](notes/).
