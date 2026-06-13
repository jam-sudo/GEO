ENV ?= geo-rnaseq
ORG ?= org.Hs.eg.db
SHELL := /bin/bash

.PHONY: help env env-update new render render-all clean

help:
	@echo "GEO RNA-seq portfolio — make targets:"
	@echo "  make env                       Create the mamba environment ($(ENV))"
	@echo "  make env-update                Update the environment from environment.yml"
	@echo "  make new ACC=GSE123456 [ORG=org.Mm.eg.db]"
	@echo "                                 Scaffold a new project from the template"
	@echo "  make render PROJ=GSE123456     Render one project's analysis.qmd -> HTML"
	@echo "  make render-all                Render every project under projects/"
	@echo "  make clean                     Remove rendered HTML/_files artifacts"
	@echo ""
	@echo "Tip: 'mamba activate $(ENV)' before render/new so R and quarto are on PATH."

env:
	mamba env create -f environment/environment.yml

env-update:
	mamba env update -f environment/environment.yml --prune

new:
	@test -n "$(ACC)" || { echo "Usage: make new ACC=GSE123456 [ORG=org.Mm.eg.db]"; exit 1; }
	Rscript scripts/new_project.R $(ACC) $(ORG)

render:
	@test -n "$(PROJ)" || { echo "Usage: make render PROJ=GSE123456"; exit 1; }
	cd projects/$(PROJ) && quarto render analysis.qmd

render-all:
	@shopt -s nullglob; \
	for d in projects/GSE*; do \
	  echo ">> Rendering $$d"; \
	  ( cd $$d && quarto render analysis.qmd ); \
	done

clean:
	find projects -name '*.html' -delete 2>/dev/null || true
	find projects -type d -name '*_files' -exec rm -rf {} + 2>/dev/null || true
	rm -rf projects/*/.quarto 2>/dev/null || true
