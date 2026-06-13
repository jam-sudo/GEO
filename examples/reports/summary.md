# Triage batch summary

| accession | title | organism | n_samples | raw_counts | suitability_class | score | decision | warnings | next_action |
|---|---|---|---|---|---|---|---|---|---|
| GSE157830 | Labile Iron Release Primes Pancreatic Cancer for Ferroptosis | Homo sapiens | 12 | yes | suitable | 100 | include |  | Scaffold and run the analysis (geo init-project … then geo run …). |
| GSE60450 | Transcriptome analysis of luminal and basal cell subpopulations in the lactating versus pregnant mammary gland | Mus musculus | 12 | yes | suitable | 100 | include |  | Scaffold and run the analysis (geo init-project … then geo run …). |
| GSE78220 | mRNA expressions in pre-treatment melanomas undergoing anti-PD-1 checkpoint inhibition therapy | Homo sapiens | 28 | no | manual_review | 65 | conditional | Normalized-only: do NOT use FPKM/TPM as DESeq2 input. Obtain raw counts from SRA/recount3/ARCHS4. | Obtain raw counts (recount3/SRA), then re-triage and scaffold. |
| GSE2034 | Breast cancer relapse free survival | Homo sapiens | 286 | no | unsuitable | 0 | exclude | Microarray data: use limma on intensities, NOT DESeq2. | Excluded from this RNA-seq framework; analyze with limma if needed. |
