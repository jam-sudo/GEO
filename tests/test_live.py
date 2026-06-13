"""Live integration tests that hit the real NCBI GEO service.

Run explicitly with:  pytest -m live
They are deselected from the default run so the normal suite stays fast/offline.
"""

import pytest

from geo_portfolio.fetch import fetch_soft
from geo_portfolio.parse import parse_soft
from geo_portfolio.suitability import assess


@pytest.mark.live
def test_live_triage_known_dataset(tmp_path):
    soft = fetch_soft("GSE157830", cache_dir=tmp_path)
    meta = parse_soft(soft)
    assert meta.n_samples == 12
    suit = assess(meta)
    assert suit.decision == "include"
