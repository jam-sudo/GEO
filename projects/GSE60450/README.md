# GSE60450 — Luminal vs basal mammary epithelium across development

> A reproducible re-analysis of mouse mammary RNA-seq comparing the two
> epithelial lineages — **luminal** (milk-producing) and **basal**
> (contractile myoepithelial) — across virgin, pregnant, and lactating stages.

## Biological question

The mammary gland is built from basal and luminal epithelial cells and remodels
across pregnancy and lactation (Fu *et al.*, 2015). **Which genes separate the
luminal from the basal lineage, accounting for developmental stage?**

## Dataset

| Field | Value |
|-------|-------|
| GEO accession | [GSE60450](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE60450) |
| Organism | *Mus musculus* (`org.Mm.eg.db`) |
| Platform | GPL13112 — Illumina HiSeq 2000 |
| Samples | 12: 2 lineages × 3 stages × 2 mice |
| Data type | **Gene-wise raw counts** (Rsubread featureCounts; integers) |
| Design formula | `~ stage + cell_type` |
| Primary contrast | luminal vs basal (n = 6 vs 6) |

Suitability report: [`SUITABILITY.md`](SUITABILITY.md) (decision: **include**).

## Suitability & metadata notes

- **Raw counts available** — single gene-wise count matrix; integers, no rounding.
- **Group labels** from GEO `source_name_ch1` / titles; count-column codes
  (`MCL1-DG…`) mapped to samples via each GSM's **supplementary-file name**
  (`GSM..._MCL1-XX_...`) — an authoritative key, not guessed from titles. See
  [`data/GSE60450_metadata_clean.csv`](data/GSE60450_metadata_clean.csv).

## How to reproduce

```bash
mamba activate geo-rnaseq
make render PROJ=GSE60450
```

## Results

**7,347 DE genes** (padj<0.05, |log2FC|>1) between luminal and basal, from
18,418 tested — the lineage divide is deep, as expected for two distinct cell
types (contrast GSE157830's ~900 genes from a single-gene knockdown).

- **Markers confirm the labels:** basal-high Krt5 (−9.0), Acta2 (−8.9), Krt14
  (−6.8); luminal-high Krt18 (+3.9), Esr1 (+2.5), Krt8 (+2.0).
- **Basal program (GO):** extracellular-matrix organization, cell-substrate
  adhesion, muscle contraction — the contractile myoepithelial phenotype.
- **Luminal program:** Tph1 (serotonin/lactation), Calca, secretory Wfdc genes.

Figures in [`results/figures/`](results/figures/); full DE table in
[`results/tables/GSE60450_DE_results.csv`](results/tables/GSE60450_DE_results.csv);
rendered report: [`analysis.html`](analysis.html).

## Limitations

- **Only 2 mice per group** — the luminal-vs-basal contrast pools to n = 6/side
  (well powered), but stage-specific contrasts (n = 2) are exploratory.
- Additive design assumes a stage-consistent lineage difference; a
  `stage:cell_type` interaction would test lineage-specific remodelling.
- Entrez IDs from the submitter's matrix; a few may be retired in current builds.
