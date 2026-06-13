# GSEXXXXXX — <short descriptive title>

> One-sentence summary of the dataset and the comparison, readable by a
> non-specialist. *Replace this line.*

## Biological question

*What is being compared, in what system, and why does it matter?*

## Dataset

| Field | Value |
|-------|-------|
| GEO accession | [GSEXXXXXX](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSEXXXXXX) |
| Organism | *fill* |
| Platform (GPL) | *fill* |
| Samples | *fill* |
| Data type | *raw counts / normalized only / microarray* (from the decision gate) |
| Design formula | `~ <group_col>` |
| Contrast(s) | *fill* |

Sample metadata is downloaded from GEO and saved verbatim to
`data/GSEXXXXXX_sample_metadata.csv` — it is never hand-edited or invented.

## How to reproduce

```bash
mamba activate geo-rnaseq          # from the repo-root environment
make render PROJ=GSEXXXXXX         # renders analysis.qmd -> analysis.html
```

## Results

Key figures (in `results/figures/`):

- `qc_library_sizes.png`, `qc_count_distribution.png` — library QC
- `qc_pca.png`, `qc_sample_correlation.png` — sample structure
- `volcano.png`, `ma_plot.png` — differential expression overview
- `top_genes_heatmap.png` — top DE genes

Tables (in `results/tables/`):

- `GSEXXXXXX_DE_results.csv` — full DE table (gene ID, symbol, log2FC, p, padj)
- `GSEXXXXXX_GO_BP_enrichment.csv` — GO enrichment

## Interpretation

*2-3 sentences on the headline biological finding.*

## Limitations

*Dataset-specific caveats — data type, sample size, confounders, annotation gaps.*

## Notes

Working notes and decisions are in `notes/`.
