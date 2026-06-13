"""Shared test fixtures: load cached GEO SOFT records from tests/fixtures."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_soft(accession: str) -> str:
    return (FIXTURES / f"{accession}.soft").read_text(encoding="utf-8")


@pytest.fixture
def soft_157830() -> str:
    return load_soft("GSE157830")


@pytest.fixture
def soft_2034() -> str:
    return load_soft("GSE2034")


@pytest.fixture
def soft_78220() -> str:
    return load_soft("GSE78220")


# A synthetic record whose grouping is encoded ONLY in titles, with a
# unique-per-sample identifier characteristic — must be treated as ambiguous.
AMBIGUOUS_SOFT = """^SERIES = GSE000001
!Series_title = Some RNA-seq study
!Series_type = Expression profiling by high throughput sequencing
!Series_supplementary_file = ftp://x/GSE000001_raw_counts.txt.gz
^SAMPLE = GSM01
!Sample_title = control_rep1
!Sample_organism_ch1 = Homo sapiens
!Sample_characteristics_ch1 = patient id: P01
!Sample_library_strategy = RNA-Seq
^SAMPLE = GSM02
!Sample_title = treated_rep1
!Sample_organism_ch1 = Homo sapiens
!Sample_characteristics_ch1 = patient id: P02
!Sample_library_strategy = RNA-Seq
"""


@pytest.fixture
def soft_ambiguous() -> str:
    return AMBIGUOUS_SOFT
