# geo_helpers.R
# ---------------------------------------------------------------------------
# Reusable helper functions for GEO RNA-seq differential-expression projects.
#
# Source this once at the top of each project's analysis.qmd:
#   source(here::here("scripts", "geo_helpers.R"))
#
# Design philosophy
#   * Each function does one thing and returns plain data structures.
#   * Nothing fabricates metadata. Metadata always comes from GEO and is
#     written to disk verbatim.
#   * Functions that require a specific data type (e.g. run_deseq2 needs raw
#     integer counts) CHECK their inputs and stop() with an explicit message
#     rather than silently producing misleading results.
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(GEOquery)
  library(Biobase)
  library(tidyverse)
  library(ggrepel)
  library(pheatmap)
  library(RColorBrewer)
})

# Null-coalescing helper (base R >= 4.4 exports this; define for older Rs).
`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a

# ---- Plot theme -------------------------------------------------------------

#' Shared ggplot theme so every figure in the portfolio looks consistent.
geo_theme <- function(base_size = 12) {
  theme_bw(base_size = base_size) +
    theme(
      panel.grid.minor = element_blank(),
      plot.title       = element_text(face = "bold"),
      legend.position  = "right",
      strip.background = element_rect(fill = "grey95")
    )
}

# Colour-blind-friendly qualitative palette (Dark2).
GEO_PALETTE <- c("#1b9e77", "#d95f02", "#7570b3", "#e7298a",
                 "#66a61e", "#e6ab02", "#a6761d", "#666666")

#' Save a ggplot to disk at publication resolution, creating dirs as needed.
save_fig <- function(plot, path, width = 7, height = 5, dpi = 300) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  ggsave(path, plot = plot, width = width, height = height, dpi = dpi)
  invisible(path)
}

# ---- Data acquisition -------------------------------------------------------

#' Download a GEO series, save its sample metadata, and (optionally) grab the
#' supplementary files. Returns a list; never invents metadata.
#'
#' @param accession A GEO series accession, e.g. "GSE123456".
#' @param dest_dir  Project data directory (raw files go in dest_dir/raw).
#' @param get_supp  Whether to download supplementary files (raw counts often
#'                  live here rather than in the series matrix).
fetch_geo <- function(accession, dest_dir, get_supp = TRUE) {
  stopifnot(is.character(accession), length(accession) == 1)
  raw_dir <- file.path(dest_dir, "raw")
  dir.create(raw_dir, recursive = TRUE, showWarnings = FALSE)

  message("Downloading series matrix for ", accession, " ...")
  gse_list <- getGEO(accession, destdir = raw_dir, GSEMatrix = TRUE, getGPL = FALSE)

  # getGEO returns one ExpressionSet per platform. Keep the first; warn if many.
  if (length(gse_list) > 1) {
    warning(accession, " spans ", length(gse_list),
            " platforms; using the first. Inspect manually if unexpected.")
  }
  eset  <- gse_list[[1]]
  pheno <- pData(eset)

  meta_path <- file.path(dest_dir, paste0(accession, "_sample_metadata.csv"))
  write.csv(pheno, meta_path, row.names = TRUE)
  message("Saved sample metadata -> ", meta_path)

  supp_files <- character(0)
  if (get_supp) {
    supp_files <- tryCatch({
      getGEOSuppFiles(accession, baseDir = raw_dir, makeDirectory = TRUE)
      list.files(file.path(raw_dir, accession), full.names = TRUE)
    }, error = function(e) {
      warning("Could not download supplementary files: ", conditionMessage(e))
      character(0)
    })
  }

  list(
    accession  = accession,
    eset       = eset,
    pheno      = pheno,
    expr       = tryCatch(exprs(eset), error = function(e) matrix(nrow = 0, ncol = 0)),
    supp_files = supp_files,
    meta_path  = meta_path
  )
}

# ---- Data-type assessment (the decision gate) -------------------------------

#' Classify what GEO actually provided so the workflow can branch correctly.
#' Returns a `geo_verdict` describing the data type and whether DESeq2 is valid.
#'
#' This is the guard that prevents treating normalized values as raw counts.
assess_data_type <- function(geo, count_file = NULL) {
  expr <- geo$expr
  supp <- geo$supp_files %||% character(0)

  # 1. Look for a raw-count supplementary file by name.
  count_pattern  <- "count|raw_counts|htseq|featurecounts|gene_counts|rsem|reads"
  count_candidates <- supp[grepl(count_pattern, basename(supp), ignore.case = TRUE)]
  if (!is.null(count_file)) count_candidates <- count_file

  # 2. Inspect the series-matrix expression values, if any are present.
  has_matrix   <- !is.null(expr) && nrow(expr) > 0 && ncol(expr) > 0
  looks_integer <- FALSE
  value_range  <- c(NA_real_, NA_real_)
  if (has_matrix) {
    vals <- expr[is.finite(expr)]
    if (length(vals) > 0) {
      value_range   <- range(vals)
      looks_integer <- all(abs(vals - round(vals)) < 1e-8) && max(vals) > 30
    }
  }

  platform <- annotation(geo$eset)

  verdict <- function(type, suitable, reason, recommendation) {
    structure(
      list(type = type, suitable_for_deseq2 = suitable, reason = reason,
           recommendation = recommendation, count_files = count_candidates,
           value_range = value_range, platform = platform),
      class = "geo_verdict")
  }

  if (length(count_candidates) > 0) {
    return(verdict("raw_counts", TRUE,
      paste0("Supplementary file(s) look like raw counts: ",
             paste(basename(count_candidates), collapse = ", ")),
      "Load the count matrix and run DESeq2 with an explicit design formula."))
  }
  if (has_matrix && looks_integer) {
    return(verdict("raw_counts", TRUE,
      "Series-matrix values are non-negative integers consistent with raw counts.",
      "Use the series-matrix counts for DESeq2 (confirm they are not rounded normalized values)."))
  }
  if (has_matrix) {
    return(verdict("normalized", FALSE,
      paste0("Series-matrix values are continuous (range ",
             signif(value_range[1], 3), " to ", signif(value_range[2], 3),
             "), consistent with normalized expression (FPKM/TPM/log2), not raw counts."),
      "Do NOT run DESeq2 on these values. Use limma on log2-normalized data, or fetch raw counts from SRA / recount3 / ARCHS4."))
  }
  verdict("unknown", FALSE,
    "No usable expression matrix in the series matrix and no recognizable count supplementary file.",
    "Inspect supplementary files manually; raw FASTQ/SRA reprocessing may be required.")
}

#' @export
print.geo_verdict <- function(x, ...) {
  cat("Data-type verdict\n")
  cat("  type:                ", x$type, "\n", sep = "")
  cat("  suitable for DESeq2: ", x$suitable_for_deseq2, "\n", sep = "")
  cat("  reason:              ", x$reason, "\n", sep = "")
  cat("  recommendation:      ", x$recommendation, "\n", sep = "")
  if (length(x$count_files)) cat("  count files:         ",
                                 paste(basename(x$count_files), collapse = ", "), "\n", sep = "")
  invisible(x)
}

# ---- Sample metadata & experimental design ----------------------------------

#' Summarize samples and surface columns that look like grouping variables
#' (vary across samples but are not unique per sample).
summarize_samples <- function(pheno) {
  is_group_like <- vapply(pheno, function(col) {
    n <- length(unique(col))
    n > 1 && n < nrow(pheno)
  }, logical(1))
  group_cols <- names(pheno)[is_group_like]
  keep <- intersect(c("title", "geo_accession", group_cols), names(pheno))
  list(
    n_samples            = nrow(pheno),
    candidate_group_cols = group_cols,
    preview              = head(pheno[, keep, drop = FALSE], 30)
  )
}

#' Given a grouping column, enumerate groups and all pairwise contrasts so the
#' analyst can choose biologically meaningful comparisons before running DE.
propose_contrasts <- function(pheno, group_col) {
  stopifnot(group_col %in% names(pheno))
  groups <- factor(pheno[[group_col]])
  tab    <- table(groups)
  combos <- if (nlevels(groups) >= 2)
    utils::combn(levels(groups), 2, simplify = FALSE) else list()
  contrasts <- lapply(combos, function(p) {
    list(factor = group_col, numerator = p[2], denominator = p[1],
         n_numerator = as.integer(tab[p[2]]), n_denominator = as.integer(tab[p[1]]))
  })
  list(group_col = group_col, group_sizes = tab, contrasts = contrasts)
}

# ---- QC plots ---------------------------------------------------------------

plot_library_sizes <- function(counts, group = NULL) {
  df <- tibble(sample = colnames(counts),
               lib_size = colSums(counts),
               group = group %||% "all")
  ggplot(df, aes(reorder(sample, lib_size), lib_size, fill = group)) +
    geom_col() +
    coord_flip() +
    scale_fill_manual(values = rep(GEO_PALETTE, length.out = length(unique(df$group)))) +
    labs(x = NULL, y = "Library size (total counts)",
         title = "Library size per sample", fill = NULL) +
    geo_theme()
}

plot_count_distribution <- function(counts, group = NULL) {
  logc <- log2(counts + 1)
  df <- as_tibble(logc, rownames = "gene") |>
    pivot_longer(-gene, names_to = "sample", values_to = "log2_count")
  df$group <- if (!is.null(group)) group[match(df$sample, colnames(counts))] else "all"
  ggplot(df, aes(sample, log2_count, fill = group)) +
    geom_boxplot(outlier.size = 0.2) +
    coord_flip() +
    labs(x = NULL, y = "log2(count + 1)",
         title = "Count distribution per sample", fill = NULL) +
    geo_theme()
}

#' PCA from a variance-stabilized or log-normalized matrix (genes x samples).
plot_pca <- function(mat, group, title = "PCA") {
  pc <- prcomp(t(mat), scale. = FALSE)
  ve <- round(100 * pc$sdev^2 / sum(pc$sdev^2), 1)
  df <- tibble(PC1 = pc$x[, 1], PC2 = pc$x[, 2],
               sample = colnames(mat), group = group)
  ggplot(df, aes(PC1, PC2, color = group, label = sample)) +
    geom_point(size = 3) +
    ggrepel::geom_text_repel(size = 3, max.overlaps = 20, show.legend = FALSE) +
    scale_color_manual(values = rep(GEO_PALETTE, length.out = length(unique(group)))) +
    labs(title = title, color = NULL,
         x = paste0("PC1 (", ve[1], "%)"),
         y = paste0("PC2 (", ve[2], "%)")) +
    geo_theme()
}

#' Sample-sample correlation heatmap (returns a pheatmap object; pass `file` to
#' save directly to disk).
plot_sample_correlation <- function(mat, group = NULL, file = NA, method = "spearman") {
  cor_mat <- cor(mat, method = method)
  ann <- if (!is.null(group))
    data.frame(group = group, row.names = colnames(mat)) else NA
  pheatmap(cor_mat,
           annotation_col = ann,
           color = colorRampPalette(brewer.pal(9, "Blues"))(100),
           main = paste0("Sample-sample ", method, " correlation"),
           filename = file)
}

# ---- Differential expression (DESeq2) ---------------------------------------

#' Run a standard DESeq2 analysis. REQUIRES raw integer counts and stops if the
#' input looks normalized, so the pipeline cannot silently misuse normalized data.
#'
#' @param counts   gene x sample integer count matrix.
#' @param coldata  data.frame of sample metadata, rownames == colnames(counts).
#' @param design   model formula, e.g. ~ condition  (explicit design).
#' @param contrast c(factor, numerator, denominator), e.g. c("condition","KO","WT").
#' @param ref_level optional reference level to relevel the contrast factor onto.
run_deseq2 <- function(counts, coldata, design, contrast, ref_level = NULL) {
  if (!requireNamespace("DESeq2", quietly = TRUE)) stop("DESeq2 is not installed.")
  counts <- as.matrix(counts)
  if (!all(abs(counts - round(counts)) < 1e-8)) {
    stop("run_deseq2() requires raw integer counts, but the matrix contains ",
         "non-integer values. This usually means the data are normalized ",
         "(FPKM/TPM/log2). Refusing to produce misleading DESeq2 results.")
  }
  storage.mode(counts) <- "integer"
  stopifnot(all(colnames(counts) == rownames(coldata)))

  dds <- DESeq2::DESeqDataSetFromMatrix(countData = counts,
                                        colData   = coldata,
                                        design    = design)
  dds <- dds[rowSums(DESeq2::counts(dds)) >= 10, ]          # pre-filter
  if (!is.null(ref_level)) {
    dds[[contrast[1]]] <- relevel(dds[[contrast[1]]], ref = ref_level)
  }
  dds <- DESeq2::DESeq(dds)
  res <- DESeq2::results(dds, contrast = contrast)

  res_df <- as.data.frame(res) |>
    tibble::rownames_to_column("gene_id") |>
    dplyr::arrange(padj)

  list(dds = dds, res = res, res_df = res_df,
       vsd = DESeq2::vst(dds, blind = FALSE))
}

volcano_plot <- function(res_df, lfc_thresh = 1, padj_thresh = 0.05,
                         label_n = 15, title = "Volcano plot") {
  df <- res_df |>
    filter(!is.na(padj)) |>
    mutate(sig = case_when(
      padj < padj_thresh & log2FoldChange >  lfc_thresh ~ "Up",
      padj < padj_thresh & log2FoldChange < -lfc_thresh ~ "Down",
      TRUE ~ "NS"))
  lab_col <- if ("symbol" %in% names(df)) "symbol" else "gene_id"
  top <- df |> filter(sig != "NS") |> slice_min(padj, n = label_n, with_ties = FALSE)
  ggplot(df, aes(log2FoldChange, -log10(padj), color = sig)) +
    geom_point(alpha = 0.6, size = 1) +
    geom_vline(xintercept = c(-lfc_thresh, lfc_thresh), linetype = "dashed", color = "grey50") +
    geom_hline(yintercept = -log10(padj_thresh), linetype = "dashed", color = "grey50") +
    ggrepel::geom_text_repel(data = top, aes(label = .data[[lab_col]]),
                             size = 3, max.overlaps = 20, show.legend = FALSE) +
    scale_color_manual(values = c(Up = "#d73027", Down = "#4575b4", NS = "grey70")) +
    labs(title = title, x = "log2 fold change",
         y = "-log10 adjusted p-value", color = NULL) +
    geo_theme()
}

ma_plot <- function(res_df, padj_thresh = 0.05, title = "MA plot") {
  df <- res_df |>
    filter(!is.na(padj), baseMean > 0) |>
    mutate(sig = ifelse(padj < padj_thresh, "Significant", "NS"))
  ggplot(df, aes(baseMean, log2FoldChange, color = sig)) +
    geom_point(alpha = 0.5, size = 1) +
    scale_x_log10() +
    geom_hline(yintercept = 0, color = "grey40") +
    scale_color_manual(values = c(Significant = "#d73027", NS = "grey70")) +
    labs(title = title, x = "mean of normalized counts (log10)",
         y = "log2 fold change", color = NULL) +
    geo_theme()
}

#' Heatmap of the top-n DE genes from a variance-stabilized object (z-scored).
top_gene_heatmap <- function(vsd, res_df, n = 30, group = NULL, file = NA,
                             id_col = "gene_id", label_col = "symbol") {
  mat <- SummarizedExperiment::assay(vsd)
  top_ids <- res_df |> filter(!is.na(padj)) |>
    slice_min(padj, n = n, with_ties = FALSE) |> pull(.data[[id_col]])
  sub <- mat[rownames(mat) %in% top_ids, , drop = FALSE]
  sub <- t(scale(t(sub)))                                  # z-score per gene
  if (!is.null(label_col) && label_col %in% names(res_df)) {
    lab <- res_df[[label_col]][match(rownames(sub), res_df[[id_col]])]
    rownames(sub) <- ifelse(is.na(lab) | lab == "", rownames(sub), lab)
  }
  ann <- if (!is.null(group))
    data.frame(group = group, row.names = colnames(sub)) else NA
  pheatmap(sub, annotation_col = ann,
           color = colorRampPalette(rev(brewer.pal(11, "RdBu")))(100),
           main = paste("Top", n, "DE genes (z-scored)"),
           filename = file, show_rownames = nrow(sub) <= 60)
}

# ---- Annotation & functional enrichment -------------------------------------

#' Map gene IDs to symbols via an organism annotation DB (e.g. org.Hs.eg.db).
#' Strips Ensembl version suffixes. Degrades gracefully if the DB is missing.
annotate_symbols <- function(res_df, orgdb = "org.Hs.eg.db",
                             keytype = "ENSEMBL", id_col = "gene_id") {
  if (!requireNamespace(orgdb, quietly = TRUE)) {
    warning(orgdb, " not installed; skipping symbol annotation.")
    res_df$symbol <- NA_character_
    return(res_df)
  }
  db  <- getExportedValue(orgdb, orgdb)
  ids <- sub("\\..*$", "", res_df[[id_col]])               # strip version suffix
  sym <- suppressMessages(AnnotationDbi::mapIds(
    db, keys = unique(ids), column = "SYMBOL",
    keytype = keytype, multiVals = "first"))
  res_df$symbol <- unname(sym[ids])
  res_df
}

#' GO biological-process over-representation on significant genes via
#' clusterProfiler. Returns NULL (with a warning) if the package is unavailable.
run_enrichment <- function(res_df, orgdb = "org.Hs.eg.db", keytype = "ENSEMBL",
                           id_col = "gene_id", padj_thresh = 0.05, lfc_thresh = 1) {
  if (!requireNamespace("clusterProfiler", quietly = TRUE)) {
    warning("clusterProfiler not installed; skipping enrichment.")
    return(NULL)
  }
  sig <- res_df |>
    filter(!is.na(padj), padj < padj_thresh, abs(log2FoldChange) > lfc_thresh)
  if (nrow(sig) < 10)
    warning("Fewer than 10 significant genes; enrichment may be unreliable.")
  genes <- unique(sub("\\..*$", "", sig[[id_col]]))
  ego <- tryCatch(
    clusterProfiler::enrichGO(gene = genes, OrgDb = orgdb, keyType = keytype,
                              ont = "BP", pvalueCutoff = 0.05, readable = TRUE),
    error = function(e) { warning(conditionMessage(e)); NULL })
  list(go_bp = ego, n_input = length(genes))
}

# ---- Output -----------------------------------------------------------------

#' Write a results table to CSV, creating the parent directory if needed.
write_results_table <- function(res_df, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  readr::write_csv(res_df, path)
  invisible(path)
}
