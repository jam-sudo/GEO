"""Download the raw count matrix that triage detected, into a project's data/raw/.

Reuses the file classification from ``suitability`` so we only fetch files that
look like raw counts — never FPKM/TPM/normalized matrices.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, List, Optional

import requests

from .parse import GeoMetadata
from .suitability import classify_file


class DataDownloadError(RuntimeError):
    pass


def raw_count_urls(meta: GeoMetadata) -> List[str]:
    """Series-level supplementary URLs whose filename classifies as raw_counts.

    Prefers gene-level counts: if both gene- and isoform-level count files exist,
    only the gene-level ones are returned (the analyses are gene-level).
    """
    counts = [u for u in meta.series_supplementary_urls
              if classify_file(os.path.basename(u)) == "raw_counts"]
    gene = [u for u in counts if "gene" in os.path.basename(u).lower()]
    isoform = [u for u in counts if "isoform" in os.path.basename(u).lower()]
    if gene and isoform:
        return gene
    return counts


def _download(url: str, dest: Path, timeout: int = 120) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as resp:
        if resp.status_code != 200:
            raise DataDownloadError(f"HTTP {resp.status_code} for {url}")
        with dest.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
    return dest


def download_counts(
    meta: GeoMetadata,
    project_dir: Path,
    overwrite: bool = False,
    progress: Optional[Callable[[str], None]] = None,
) -> List[Path]:
    """Download detected raw-count files into <project_dir>/data/raw/.

    Returns the list of local paths. Raises DataDownloadError if none detected.
    """
    urls = raw_count_urls(meta)
    if not urls:
        raise DataDownloadError(
            "No raw-count supplementary file detected for this series "
            "(GEO may provide only FPKM/TPM, or counts live in SRA/recount3)."
        )
    raw_dir = Path(project_dir) / "data" / "raw"
    out: List[Path] = []
    for url in urls:
        dest = raw_dir / os.path.basename(url)
        if dest.exists() and not overwrite:
            if progress:
                progress(f"exists, skipping {dest.name}")
            out.append(dest)
            continue
        if progress:
            progress(f"downloading {dest.name}")
        out.append(_download(url, dest))
    return out
