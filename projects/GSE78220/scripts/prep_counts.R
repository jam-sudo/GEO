#!/usr/bin/env Rscript
# Fetch raw gene-level counts for GSE78220 from recount3 (study SRP070710),
# join to the cleaned response metadata, and save a local count matrix so the
# report is reproducible without re-hitting recount3 at render time.
#
# This is the "promotion" step: GSE78220 was CONDITIONAL (FPKM-only on GEO);
# recount3 provides the raw counts that make DESeq2 valid.

suppressPackageStartupMessages({
  library(recount3)
  library(SummarizedExperiment)
})

OUT_COUNTS <- "projects/GSE78220/data/GSE78220_recount3_counts.rds"
OUT_META   <- "projects/GSE78220/data/GSE78220_metadata_clean.csv"

resp <- read.csv(OUT_META, stringsAsFactors = FALSE)        # geo_accession, patient, response_raw, response, sra(SRX)

projs <- available_projects()
pinfo <- projs[projs$project == "SRP070710" & projs$file_source == "sra", ]
stopifnot(nrow(pinfo) >= 1)
rse <- create_rse(pinfo[1, ])
assay(rse, "counts") <- transform_counts(rse)               # scaled read counts

cd <- as.data.frame(colData(rse))
# Find the column holding the SRA experiment (SRX) accession.
srx_col <- names(cd)[vapply(cd, function(x) any(grepl("^SRX[0-9]+$", as.character(x))), logical(1))][1]
cat("Joining recount3 colData on:", srx_col, "\n")
cd$.srx <- as.character(cd[[srx_col]])

keep <- match(resp$sra, cd$.srx)
if (any(is.na(keep))) {
  cat("WARNING: unmatched SRX:\n"); print(resp$sra[is.na(keep)])
}
keep <- keep[!is.na(keep)]
rse <- rse[, keep]

counts <- round(assay(rse, "counts"))
storage.mode(counts) <- "integer"

# Align metadata to the kept/ordered recount3 columns, label columns by patient.
meta <- resp[match(cd$.srx[keep], resp$sra), ]
rownames(meta) <- meta$patient
colnames(counts) <- meta$patient

rd <- as.data.frame(rowData(rse))
gene_id <- rownames(rse)
saveRDS(list(counts = counts, meta = meta, gene_id = gene_id, rowdata = rd), OUT_COUNTS)

cat("Saved", OUT_COUNTS, ":", nrow(counts), "genes x", ncol(counts), "samples\n")
cat("Groups:\n"); print(table(meta$response))
