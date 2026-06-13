#!/usr/bin/env Rscript
# Scaffold a new project folder from templates/project_template.
#
# Usage (run from the repo root, e.g. via `make new ACC=GSE123456`):
#   Rscript scripts/new_project.R GSE123456 [organism_db]
#
# organism_db defaults to org.Hs.eg.db (human). Use org.Mm.eg.db for mouse, etc.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript scripts/new_project.R <GSE_ACCESSION> [organism_db]")
}
acc <- args[1]
org <- if (length(args) >= 2) args[2] else "org.Hs.eg.db"

if (!grepl("^GSE[0-9]+$", acc)) {
  stop("Accession should look like 'GSE123456'. Got: ", acc)
}

template <- file.path("templates", "project_template")
dest     <- file.path("projects", acc)

if (!dir.exists(template)) stop("Template not found: ", template,
                                " (run from the repo root).")
if (dir.exists(dest))      stop(dest, " already exists. Remove it first or pick another accession.")

dir.create(dest, recursive = TRUE)
ok <- file.copy(list.files(template, full.names = TRUE), dest, recursive = TRUE)
if (!all(ok)) stop("Failed to copy some template files.")

# Substitute placeholders in the text files.
for (f in c(file.path(dest, "SUITABILITY.md"),
            file.path(dest, "analysis.qmd"),
            file.path(dest, "README.md"))) {
  txt <- readLines(f, warn = FALSE)
  txt <- gsub("GSEXXXXXX",   acc, txt, fixed = TRUE)
  txt <- gsub("ORGANISM_DB", org, txt, fixed = TRUE)
  writeLines(txt, f)
}

cat("Created project:", dest, "\n")
cat("Triage-first workflow:\n")
cat("  1. Inspect the GEO record and FILL", file.path(dest, "SUITABILITY.md"),
    "\n     (organism, files, raw counts?, replicates, design, decision).\n")
cat("  2. Rebuild the cross-dataset table:  make triage\n")
cat("  3. ONLY if decision: include — customize", file.path(dest, "analysis.qmd"),
    "and run:\n       make render PROJ=", acc, "\n", sep = "")
