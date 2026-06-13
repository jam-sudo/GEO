"""Suitability triage: data-type gate, transparent scoring, and factor inference.

Mirrors the philosophy of the R framework's ``assess_data_type`` and the
SUITABILITY.md schema, but adds the richer scoring / factor inference the CLI
needs. Conservative by design: when uncertain, returns ``manual_review``.

Decision mapping (to the existing framework's vocabulary):
    suitable      -> include
    manual_review -> conditional
    unsuitable    -> exclude
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .parse import GeoMetadata, Sample

# --- File classification patterns --------------------------------------------

_RAW_COUNT_RE = re.compile(
    r"(?:^|[._-])(counts?|genewisecounts|htseq|featurecounts|rawcounts?|readcounts?|estcounts?)",
    re.IGNORECASE,
)
_NORMALIZED_RE = re.compile(r"(fpkm|tpm|rpkm|normali[sz]ed|\bcpm\b|rlog|\bvst\b)", re.IGNORECASE)
_ARRAY_FILE_RE = re.compile(r"\.cel(\.gz)?$|_raw\.tar$", re.IGNORECASE)


def classify_file(name: str) -> str:
    """Classify a supplementary file by its name."""
    n = name.lower()
    # FPKM/TPM take precedence in naming even if 'counts' appears elsewhere.
    if _NORMALIZED_RE.search(n) and not _RAW_COUNT_RE.search(n):
        if "fpkm" in n:
            return "fpkm"
        if "tpm" in n:
            return "tpm"
        if "rpkm" in n:
            return "rpkm"
        return "normalized"
    if _RAW_COUNT_RE.search(n):
        return "raw_counts"
    if name.lower().endswith("_raw.tar"):
        return "archive"
    if name.lower().endswith((".cel", ".cel.gz")):
        return "microarray_raw"
    return "other"


def classify_files(names: List[str]) -> List[dict]:
    seen = {}
    for name in names:
        if name not in seen:
            seen[name] = {"name": name, "type": classify_file(name)}
    return list(seen.values())


# --- Assay detection ----------------------------------------------------------

def infer_assay(meta: GeoMetadata) -> str:
    """Return one of: rna_seq, microarray, single_cell, other."""
    st = (meta.series_type or "").lower()
    title = (meta.title or "").lower()
    summary = (meta.summary or "").lower()
    strategies = {s.library_strategy.lower() for s in meta.samples if s.library_strategy}

    if "single cell" in title or "single-cell" in title or "scrna" in title or "single cell" in summary:
        return "single_cell"
    if "by array" in st or "rna-seq" not in strategies and "by array" in st:
        return "microarray"
    if "high throughput sequencing" in st or "rna-seq" in strategies or "transcriptomic" in strategies:
        return "rna_seq"
    if "by array" in st:
        return "microarray"
    return "other"


# --- Factor inference ---------------------------------------------------------

_FACTOR_KEYWORDS = {
    "treatment": ["treat", "agent", "dose", "drug", "stimul", "compound", "dox", "ligand", "inhibitor"],
    "genotype": ["genotype", "variation", "knockdown", "knockout", "shrna", "sirna", "crispr",
                 "mutation", "transfect", "guide", "overexpress"],
    "disease": ["disease", "diagnosis", "tumor", "tumour", "cancer", "status", "condition",
                "subtype", "grade", "stage", "phenotype", "response"],
    "timepoint": ["time", "day", "hour", " hr", "week", "passage", "age"],
    "tissue": ["tissue", "organ", "anatomic", "biopsy", "site", "location"],
    "cell_line": ["cell line", "cell type", "cell-line", "cell_line"],
    "batch": ["batch", "replicate", "run", "lane", "donor", "patient", "individual", "subject"],
}


@dataclass
class Factor:
    name: str          # inferred factor category
    source_key: str    # the GEO characteristics key it came from
    levels: Dict[str, int] = field(default_factory=dict)
    ambiguous: bool = False
    note: str = ""

    @property
    def n_levels(self) -> int:
        return len(self.levels)


def _categorize_key(key: str) -> Optional[str]:
    k = key.lower()
    for factor, words in _FACTOR_KEYWORDS.items():
        if any(w in k for w in words):
            return factor
    return None


def infer_factors(samples: List[Sample]) -> List[Factor]:
    """Infer experimental factors from sample characteristics keys.

    A characteristics key whose values vary across samples (but are not unique
    per sample) is a candidate grouping factor. Keys that map to no known factor
    category, or that are unique per sample (identifiers), are reported as
    ambiguous rather than guessed.
    """
    n = len(samples)
    # Gather value distribution per characteristics key.
    keyvals: Dict[str, List[str]] = {}
    for s in samples:
        for k, v in s.characteristics.items():
            keyvals.setdefault(k, []).append(v)

    factors: List[Factor] = []
    for key, vals in keyvals.items():
        levels: Dict[str, int] = {}
        for v in vals:
            levels[v] = levels.get(v, 0) + 1
        n_levels = len(levels)
        category = _categorize_key(key)

        if n_levels <= 1:
            continue  # constant — not a grouping factor
        if n_levels >= n:
            # unique-per-sample → identifier-like; record but mark ambiguous
            factors.append(Factor(name=category or "unknown", source_key=key,
                                   levels={}, ambiguous=True,
                                   note="unique per sample (identifier-like); not a usable grouping factor"))
            continue
        factors.append(Factor(name=category or "unknown", source_key=key,
                              levels=levels, ambiguous=category is None,
                              note="" if category else "characteristics key did not map to a known factor type"))
    return factors


# --- Suitability scoring ------------------------------------------------------

@dataclass
class Suitability:
    assay: str
    suitability_class: str          # suitable | manual_review | unsuitable
    decision: str                   # include | conditional | exclude
    score: int                      # 0-100, transparent
    reasons: List[dict] = field(default_factory=list)   # {delta, text}
    warnings: List[str] = field(default_factory=list)
    raw_counts_available: str = "unknown"   # yes | no | unknown
    normalized_values_present: str = "unknown"
    processed_files: List[dict] = field(default_factory=list)
    factors: List[Factor] = field(default_factory=list)
    groups: List[dict] = field(default_factory=list)
    min_replicates_per_group: int = 0
    metadata_clarity: str = "unknown"
    possible_contrasts: List[str] = field(default_factory=list)
    recommended_design: str = ""
    de_method: str = ""
    next_action: str = ""


def _pick_grouping_factor(factors: List[Factor]) -> Optional[Factor]:
    """Choose the most plausible primary grouping factor."""
    usable = [f for f in factors if not f.ambiguous and f.n_levels >= 2]
    if not usable:
        return None
    priority = ["genotype", "treatment", "disease", "timepoint", "tissue", "cell_line"]
    usable.sort(key=lambda f: (priority.index(f.name) if f.name in priority else 99, f.n_levels))
    return usable[0]


def _orgdb_for(organisms: List[str]) -> str:
    org = (organisms[0] if organisms else "").lower()
    if "mus musculus" in org:
        return "org.Mm.eg.db"
    if "rattus" in org:
        return "org.Rn.eg.db"
    if "homo sapiens" in org:
        return "org.Hs.eg.db"
    return "org.Hs.eg.db"


def assess(meta: GeoMetadata) -> Suitability:
    """Run the full suitability assessment for a parsed GEO record."""
    assay = infer_assay(meta)
    files = classify_files(meta.all_supplementary_files)
    types = {f["type"] for f in files}
    raw_counts = "raw_counts" in types
    normalized = bool(types & {"fpkm", "tpm", "rpkm", "normalized"})

    factors = infer_factors(meta.samples)
    grouping = _pick_grouping_factor(factors)
    if grouping:
        groups = [{"name": lvl, "n_replicates": cnt} for lvl, cnt in grouping.levels.items()]
        min_reps = min(grouping.levels.values())
        levels = list(grouping.levels)
        contrasts = [f"{levels[i]} vs {levels[j]}"
                     for i in range(len(levels)) for j in range(i + 1, len(levels))][:6]
        metadata_clarity = "clear"
    else:
        groups, min_reps, contrasts = [], 0, []
        metadata_clarity = "messy" if meta.samples else "unknown"

    reasons: List[dict] = []
    warnings: List[str] = []
    score = 50

    def add(delta: int, text: str):
        nonlocal score
        score += delta
        reasons.append({"delta": delta, "text": text})

    # 1) Assay gate.
    if assay == "microarray":
        add(-40, "Microarray assay (Expression profiling by array) — not count-based.")
        warnings.append("Microarray data: use limma on intensities, NOT DESeq2.")
        suit_class, de_method = "unsuitable", "limma (microarray)"
        raw_counts_str, norm_str = "no", "yes" if normalized else "unknown"
    elif assay == "single_cell":
        add(-10, "Single-cell assay — bulk DESeq2 not directly applicable (needs pseudobulk).")
        warnings.append("Single-cell data: pseudobulk or scRNA tools required, not bulk DESeq2.")
        suit_class, de_method = "manual_review", "manual review (single-cell)"
        raw_counts_str = "yes" if raw_counts else "unknown"
        norm_str = "yes" if normalized else "unknown"
    elif assay == "rna_seq":
        add(10, "Bulk RNA-seq assay.")
        if raw_counts:
            add(30, "Raw count file detected in supplementary files.")
            suit_class, de_method = "suitable", "DESeq2"
            raw_counts_str, norm_str = "yes", "yes" if normalized else "no"
        elif normalized:
            add(-15, "Only normalized values (FPKM/TPM/RPKM) found; no raw counts in the deposit.")
            warnings.append("Normalized-only: do NOT use FPKM/TPM as DESeq2 input. "
                            "Obtain raw counts from SRA/recount3/ARCHS4.")
            suit_class, de_method = "manual_review", "DESeq2 (requires raw counts; FPKM not valid input)"
            raw_counts_str, norm_str = "no", "yes"
        else:
            add(-10, "No recognizable processed expression file; counts may need re-derivation.")
            warnings.append("No processed matrix detected; reprocess SRA reads to get counts.")
            suit_class, de_method = "manual_review", "DESeq2 (requires raw counts)"
            raw_counts_str, norm_str = "unknown", "no"
    else:
        add(-10, "Assay type could not be determined from the series record.")
        warnings.append("Unknown assay type — manual review required.")
        suit_class, de_method = "manual_review", "manual review"
        raw_counts_str = "yes" if raw_counts else "unknown"
        norm_str = "yes" if normalized else "unknown"

    # 2) Replication (only meaningful when counts could be available).
    if suit_class != "unsuitable":
        if grouping and min_reps >= 3:
            add(10, f"Grouping factor '{grouping.name}' has >=3 replicates per level.")
        elif grouping and min_reps == 2:
            add(3, f"Grouping factor '{grouping.name}' has only 2 replicates per level.")
            warnings.append("Only 2 replicates per group — low power; treat fine-grained contrasts as exploratory.")
        else:
            add(-10, "No clear replicated grouping factor in sample characteristics.")
            warnings.append("Grouping factor ambiguous / not found in characteristics — manual curation required.")

    # 3) Metadata clarity.
    if metadata_clarity == "clear":
        add(10, f"Groups encoded in characteristics field ('{grouping.source_key}').")
    else:
        add(-10, "Groups not clearly encoded in characteristics (avoid guessing from titles).")

    # A suitable RNA-seq dataset still needs replication to actually run DESeq2.
    if suit_class == "suitable" and (not grouping or min_reps < 2):
        suit_class = "manual_review"
        warnings.append("Raw counts present but no replicated group detected — manual review before DESeq2.")

    score = max(0, min(100, score))
    decision = {"suitable": "include", "manual_review": "conditional", "unsuitable": "exclude"}[suit_class]

    # Recommended design (conservative).
    if suit_class == "unsuitable":
        recommended_design = "n/a (excluded)"
    elif grouping:
        batch = next((f for f in factors if f.name == "batch" and not f.ambiguous), None)
        recommended_design = f"~ {batch.name} + {grouping.name}" if batch else f"~ {grouping.name}"
    else:
        recommended_design = "manual review required"

    # Next action.
    if suit_class == "suitable":
        next_action = "Scaffold and run the analysis (geo init-project … then geo run …)."
    elif assay == "microarray":
        next_action = "Excluded from this RNA-seq framework; analyze with limma if needed."
    elif assay == "rna_seq" and normalized and not raw_counts:
        next_action = "Obtain raw counts (recount3/SRA), then re-triage and scaffold."
    else:
        next_action = "Manually curate sample groups / data type, then re-triage."

    return Suitability(
        assay=assay, suitability_class=suit_class, decision=decision, score=score,
        reasons=reasons, warnings=warnings,
        raw_counts_available=raw_counts_str, normalized_values_present=norm_str,
        processed_files=files, factors=factors, groups=groups,
        min_replicates_per_group=min_reps, metadata_clarity=metadata_clarity,
        possible_contrasts=contrasts, recommended_design=recommended_design,
        de_method=de_method, next_action=next_action,
    )


def orgdb_for(meta: GeoMetadata) -> str:
    return _orgdb_for(meta.organisms)
