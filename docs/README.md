# Methodology & conventions

This document explains the analysis conventions every project in the portfolio
follows, so results are comparable and reproducible across datasets.

## The decision gate

GEO deposits are inconsistent: some series provide raw counts, others only
normalized values (FPKM/TPM/log2), others are microarray. **Standard DESeq2
requires raw integer counts.** Every project therefore runs
`assess_data_type()` *before* differential expression and branches:

| Verdict | What we do |
|---------|------------|
| `raw_counts` | Full DESeq2 workflow with an explicit design formula. |
| `normalized` | **No DESeq2.** Document the limitation; optionally a limma analysis on log2 values, clearly labelled as such. |
| `microarray` / `unknown` | Flag the dataset as not standard RNA-seq DE and explain why; QC only, or fetch raw counts from SRA/recount3/ARCHS4. |

`run_deseq2()` independently re-checks that the count matrix is integer and
**stops** if it is not — a second guard against misusing normalized data.

## Standard workflow per dataset

0. **Suitability report (triage gate, before any code)** — inspect the GEO
   record and fill `projects/<ACC>/SUITABILITY.md`: organism, assay, sample
   count, available processed files, raw-counts/normalized availability,
   replicate counts per group, metadata clarity, possible contrasts, the
   recommended statistical design, and an explicit **include / conditional /
   exclude** decision with reasons. Its YAML front-matter feeds the
   cross-dataset table (`make triage` → [`TRIAGE.md`](TRIAGE.md)). Group labels
   come from `characteristics_ch1.*` fields, never from sample titles. DE
   proceeds **only** when `decision: include`.
1. **Acquire** — `fetch_geo()` downloads the series matrix + supplementary files
   and writes sample metadata to disk verbatim. Metadata is never invented.
2. **Assess** — `assess_data_type()` confirms the verdict programmatically.
3. **Inspect design** — `summarize_samples()` + `propose_contrasts()` surface
   grouping columns and valid pairwise comparisons; the analyst picks a
   biologically meaningful contrast and an explicit design formula.
4. **QC** — library sizes, count distribution, PCA, sample-correlation heatmap.
5. **DE** (raw counts only) — DESeq2 → results table (ID, symbol, log2FC, p,
   padj), volcano, MA plot, top-gene heatmap.
6. **Annotate & enrich** — map IDs to symbols; GO/KEGG over-representation.
7. **Interpret & document limitations** — every report ends with a Limitations
   section.

## Thresholds (defaults; override per dataset with justification)

- Pre-filter: genes with total count `>= 10`.
- Significance: `padj < 0.05` and `|log2FoldChange| > 1`.
- PCA/heatmaps use DESeq2 variance-stabilizing transform (`vst`).
- Enrichment: GO BP, `pvalueCutoff = 0.05`, Benjamini-Hochberg.

## Reproducibility

- One mamba environment (`environment/environment.yml`) pins R, Bioconductor,
  and Quarto for the whole repo.
- Every report embeds `sessionInfo()`.
- Re-run any project with `make render PROJ=GSE...`.

## Adding a dataset

```bash
make new ACC=GSE123456 ORG=org.Hs.eg.db   # ORG defaults to human
make render PROJ=GSE123456                 # first render downloads data + prints the verdict
```

Then edit `projects/GSE123456/analysis.qmd`: fill the biological question, set
the count-loading chunk, and set `params$group_col` / `params$contrast`.
