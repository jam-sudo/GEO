# GSE78220 — Anti-PD-1 responders vs non-responders (melanoma)

> A reproducible re-analysis asking which genes in **pre-treatment** melanoma
> tumors differ between patients who later respond vs don't respond to anti-PD-1
> immunotherapy. **This dataset required promotion:** GEO deposits only FPKM, so
> raw counts were obtained from recount3 to make DESeq2 valid.

## The judgment story (why this project exists)

GSE78220 was first triaged **CONDITIONAL** — it is genuine RNA-seq, but the only
expression file on GEO is `GSE78220_PatientFPKM.xlsx` (FPKM), which must **not**
go into DESeq2. Instead of forcing a count model onto normalized values, raw
gene counts were pulled from **recount3** (study **SRP070710**), promoting the
dataset to **INCLUDE**. See [`SUITABILITY.md`](SUITABILITY.md).

## Dataset

| Field | Value |
|-------|-------|
| GEO accession | [GSE78220](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE78220) |
| Organism | *Homo sapiens* |
| Platform | GPL11154 — Illumina HiSeq 2000 |
| Samples | 28 pre-treatment melanoma biopsies |
| Counts source | **recount3** (SRP070710); GEO deposit is FPKM-only |
| Groups | 15 responders (CR/PR) vs 13 non-responders (PD) |
| Design | `~ response` |

## Reproduce

```bash
mamba activate geo-rnaseq
Rscript projects/GSE78220/scripts/prep_metadata.R   # response labels from GEO characteristics
Rscript projects/GSE78220/scripts/prep_counts.R     # raw counts from recount3
make render PROJ=GSE78220
```

## Metadata handling (messy → clean)

GEO's `characteristics_ch1.*` fields are **ragged** (the response field is at
different positions per sample), so response was extracted by scanning all
characteristics columns ([`scripts/prep_metadata.R`](scripts/prep_metadata.R))
and dichotomized from RECIST: responder = CR/PR, non-responder = PD. GEO samples
were joined to recount3 via SRA experiment (SRX) accessions.

## Results

**415 DE genes** (padj<0.05, |log2FC|>1) of 30,348 tested — a modest signal, as
expected for an immunotherapy-response phenotype.

- Genes **higher in non-responders** include MMP1, FOXC2, and ECM genes; GO is
  led by **extracellular-matrix organization, vessel-diameter regulation, and
  muscle contraction**.
- This recapitulates the **IPRES** (Innate anti-PD-1 Resistance)
  mesenchymal/ECM/angiogenesis signature from the original study — external
  validation that the recount3-based analysis is biologically sound.

Figures: [`results/figures/`](results/figures/); DE table:
[`results/tables/GSE78220_DE_results.csv`](results/tables/GSE78220_DE_results.csv);
report: [`analysis.html`](analysis.html).

## Limitations

- Counts are recount3's uniform SRA reprocessing, not the authors' pipeline.
- Heterogeneous clinical cohort (tumor purity, site, BRAF/NRAS/NF1) not modelled.
- Pt27A/Pt27B are two biopsies from one patient (mild non-independence).
- RECIST dichotomization (CR/PR vs PD) is one of several reasonable groupings.
