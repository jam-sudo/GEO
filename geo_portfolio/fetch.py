"""Fetch GEO metadata as SOFT text, with local caching.

We deliberately use the two lightweight ``acc.cgi`` endpoints and AVOID
``targ=all`` (which drags in the full platform probe table — ~1M lines):

* ``targ=self`` → the series record (title, summary, type, supplementary files, platform id)
* ``targ=gsm``  → all samples' metadata (titles, characteristics, library strategy)

The concatenation of the two is cached under ``cache_dir/<acc>.soft`` and reused.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import requests

GEO_ACC_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
DEFAULT_CACHE = ".geo_cache"

_ACC_RE = re.compile(r"^GSE\d+$")


class GeoFetchError(RuntimeError):
    """Raised when GEO metadata cannot be retrieved."""


def validate_accession(accession: str) -> bool:
    """Return True for a syntactically valid GEO *series* accession (GSE…)."""
    return bool(_ACC_RE.match(accession or ""))


def _get(accession: str, targ: str, timeout: int, retries: int = 3) -> str:
    params = {"acc": accession, "targ": targ, "view": "brief", "form": "text"}
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(GEO_ACC_URL, params=params, timeout=timeout)
            if resp.status_code == 200 and resp.text.strip():
                # GEO returns HTTP 200 with an error body for unknown accessions.
                if "Could not find a publicly available" in resp.text:
                    raise GeoFetchError(
                        f"{accession}: GEO reports no public record for this accession."
                    )
                return resp.text
            last_err = GeoFetchError(
                f"{accession} (targ={targ}): HTTP {resp.status_code}"
            )
        except requests.RequestException as exc:  # network-level failure
            last_err = exc
        time.sleep(1.5 * (attempt + 1))
    raise GeoFetchError(f"Failed to fetch {accession} (targ={targ}): {last_err}")


def fetch_soft(
    accession: str,
    cache_dir: str | Path = DEFAULT_CACHE,
    refresh: bool = False,
    timeout: int = 60,
) -> str:
    """Return combined SOFT text for *accession*, fetching and caching if needed.

    Set ``refresh=True`` to bypass the cache and re-download.
    """
    if not validate_accession(accession):
        raise GeoFetchError(
            f"'{accession}' is not a valid GEO series accession (expected like 'GSE123456')."
        )
    cache_path = Path(cache_dir) / f"{accession}.soft"
    if cache_path.exists() and not refresh:
        return cache_path.read_text(encoding="utf-8", errors="replace")

    series = _get(accession, "self", timeout)
    samples = _get(accession, "gsm", timeout)
    text = series.rstrip() + "\n" + samples

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text, encoding="utf-8")
    return text
