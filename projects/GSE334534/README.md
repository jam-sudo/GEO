# GSE334534 — IgG-positive vs IgG-negative pancreatic cancer cells

> A reproducible re-analysis of PL45 pancreatic-cancer cells sorted by surface
> **IgG binding**, asking which genes differ between the IgG-positive and
> IgG-negative fractions. Found via `geo` discovery + triage, then curated.

## Biological question

PL45 cells (two single-cell clones, A1 and A14) were sorted into **IgG-positive**
vs **IgG-negative** fractions to find transcriptional determinants of humoral-
immunity phenotypes. **Which genes differ between IgG-positive and IgG-negative
cells, consistently across the two clones?**

## Dataset

| Field | Value |
|-------|-------|
| GEO accession | [GSE334534](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE334534) |
| Organism | *Homo sapiens* |
| Platform | GPL34284 (Illumina, RNA-seq) |
| Samples | 12: 2 clones (A1, A14) × 2 sorts (IgG_Negative/Positive) × 3 reps |
| Data type | **Gene-level RSEM expected counts** (rounded for DESeq2) |
| Design formula | `~ clone + treatment` |
| Primary contrast | IgG_Positive vs IgG_Negative |

## Suitability & curation notes

See [`SUITABILITY.md`](SUITABILITY.md). This dataset needed several careful calls:

- **No GEO series matrix** (`matrix/` → 404) — read the local RSEM count file
  directly instead of `getGEO()`.
- **RSEM expected counts are fractional** → rounded to integers for DESeq2.
- **`cell line` is constant (PL45)**; the clone (A1/A14) is parsed from the
  sample name (documented assumption), used as a balanced covariate.
- **Batch is partially confounded with the IgG sort**, so the design is
  `~ clone + treatment`, *not* `~ batch + treatment` — recorded as a limitation.

## How to reproduce

```bash
mamba activate geo-rnaseq

# 1. Download the RSEM count matrix from GEO (data/raw/ is gitignored).
mkdir -p projects/GSE334534/data/raw
curl -L -o projects/GSE334534/data/raw/GSE334534_genes_expected_counts_all_samples.txt.gz \
  https://ftp.ncbi.nlm.nih.gov/geo/series/GSE334nnn/GSE334534/suppl/GSE334534_genes_expected_counts_all_samples.txt.gz

# 2. Render.
make render PROJ=GSE334534
```

## Results

**437 DE genes** (padj<0.05, |log2FC|>1) of 15,434 tested — a **modest** signal.

- Higher in IgG-positive: epithelial/differentiation genes (GRHL2, SORL1, GALNT5,
  TNS4, SH3TC2).
- **Read with caution:** several top features are rRNA/snRNA/pseudogenes
  (RNA5-8S5, RNU5F-1), and GO enrichment is dominated by taste-receptor / snRNP
  terms — likely technical artifacts. Combined with the partial batch–sort
  confounding, the IgG-sort effect is real but modest, not a headline finding.

Figures in [`results/figures/`](results/figures/); DE table in
[`results/tables/GSE334534_DE_results.csv`](results/tables/GSE334534_DE_results.csv);
report: [`analysis.html`](analysis.html).

## Limitations

- **Batch partially confounded with the IgG sort** → not identifiable; reported
  effect may carry residual batch signal.
- RSEM expected counts rounded; clone parsed from sample name (not a
  characteristics field).
- Noisy top features (rRNA/snRNA) suggest rRNA filtering would sharpen the signal.
- 2 clones, n=3 per clone×sort — limited sampling.

## Why this dataset is in the portfolio

It's a deliberate example of a dataset that **passes triage** (raw counts,
balanced design) yet yields a **modest, caveat-heavy** result — demonstrating
honest reporting rather than only headline findings.
