import json

import yaml

from geo_portfolio.parse import parse_soft
from geo_portfolio.report import to_json, to_markdown
from geo_portfolio.suitability import assess

REQUIRED_FM_KEYS = [
    "accession", "title", "organism", "assay_type", "platform", "n_samples",
    "processed_files", "raw_counts_available", "normalized_values_present",
    "groups", "min_replicates_per_group", "metadata_clarity",
    "possible_contrasts", "recommended_design", "de_method", "decision",
]


def _front_matter(md: str) -> dict:
    assert md.startswith("---")
    _, _, rest = md.partition("---")
    fm, _, _ = rest.partition("\n---")
    return yaml.safe_load(fm)


def test_markdown_frontmatter_matches_schema(soft_157830):
    meta = parse_soft(soft_157830)
    md = to_markdown(meta, assess(meta))
    fm = _front_matter(md)
    for key in REQUIRED_FM_KEYS:
        assert key in fm, f"missing front-matter key: {key}"
    # yes/no must be strings, not booleans (so build_triage.R reads them correctly)
    assert isinstance(fm["raw_counts_available"], str)
    assert fm["raw_counts_available"] == "yes"
    assert fm["decision"] == "include"


def test_markdown_has_readable_sections(soft_157830):
    meta = parse_soft(soft_157830)
    md = to_markdown(meta, assess(meta))
    for heading in ["# Dataset suitability report", "## Data type",
                    "## Suitability scoring", "## Recommended design"]:
        assert heading in md


def test_json_is_valid_and_structured(soft_78220):
    meta = parse_soft(soft_78220)
    data = json.loads(to_json(meta, assess(meta)))
    assert data["accession"] == "GSE78220"
    assert data["decision"] == "conditional"
    assert "suitability_score" in data
    assert "warnings" in data and isinstance(data["warnings"], list)
    assert "factors" in data
