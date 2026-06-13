#!/usr/bin/env Rscript
# Build a cleaned response metadata table for GSE78220 from the GEO pData.
# The characteristics columns are RAGGED (the same field sits at different
# positions across samples), so we scan ALL characteristics columns per sample.

p <- readRDS("projects/GSE78220/data/raw/pData.rds")
chcols <- names(p)[grepl("characteristics", names(p))]

# Pull the value of a "key: value" characteristic, searching every char column.
get_char <- function(i, key) {
  vals <- as.character(unlist(p[i, chcols]))
  hit  <- vals[grepl(paste0("^", key), vals, ignore.case = TRUE)]
  if (length(hit) == 0) return(NA_character_)
  trimws(sub(paste0("^", key, "\\s*:?\\s*"), "", hit[1], ignore.case = TRUE))
}

n <- nrow(p)
response_raw <- vapply(seq_len(n), get_char, character(1), key = "anti-pd-1 response")

# Dichotomize RECIST response (documented assumption):
#   Responder     = Complete Response, Partial Response
#   Non-responder = Progressive Disease
# (Stable Disease, if present, is ambiguous and handled explicitly below.)
response <- dplyr::case_when(
  grepl("Complete Response|Partial Response", response_raw) ~ "responder",
  grepl("Progressive Disease",               response_raw) ~ "non_responder",
  grepl("Stable Disease",                    response_raw) ~ "stable_disease",
  TRUE ~ NA_character_
)

# SRA accession from the relation field(s) (for recount3 join).
relcols <- grep("relation", names(p), value = TRUE, ignore.case = TRUE)
sra <- vapply(seq_len(n), function(i) {
  v <- as.character(unlist(p[i, relcols]))
  h <- v[grepl("SRA|SRX|SRR", v)]
  if (length(h) == 0) NA_character_ else sub(".*?(SR[XPR][0-9]+).*", "\\1", h[1])
}, character(1))

meta <- data.frame(
  geo_accession = p$geo_accession,
  patient       = p$title,
  response_raw  = response_raw,
  response      = response,
  sra           = sra,
  stringsAsFactors = FALSE
)

cat("Response (raw) table:\n");   print(table(response_raw, useNA = "ifany"))
cat("\nResponse (dichotomized):\n"); print(table(response, useNA = "ifany"))
cat("\n"); print(meta, row.names = FALSE)

write.csv(meta, "projects/GSE78220/data/GSE78220_metadata_clean.csv", row.names = FALSE)
cat("\nWrote projects/GSE78220/data/GSE78220_metadata_clean.csv\n")
