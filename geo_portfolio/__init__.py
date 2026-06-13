"""geo_portfolio — CLI/orchestration layer for the GEO RNA-seq reanalysis portfolio.

This package is intentionally thin: it triages GEO accessions and orchestrates the
*existing* R/Quarto analysis framework (templates/, scripts/, environment/). It does
NOT reimplement differential-expression analysis.
"""

__version__ = "0.1.0"
