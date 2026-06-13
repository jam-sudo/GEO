"""Parse GEO SOFT text into structured dataclasses.

Pure functions only — no network. This makes parsing trivially testable from
fixture files.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Sample:
    gsm: str
    title: str = ""
    source_name: str = ""
    organism: str = ""
    library_strategy: str = ""
    characteristics: Dict[str, str] = field(default_factory=dict)
    # When a characteristic key repeats with different values within one sample,
    # extra values are preserved here so nothing is silently dropped.
    extra_characteristics: List[str] = field(default_factory=list)
    supplementary_files: List[str] = field(default_factory=list)


@dataclass
class GeoMetadata:
    accession: str = ""
    title: str = ""
    summary: str = ""
    overall_design: str = ""
    series_type: str = ""
    platform_id: str = ""
    platform_title: str = ""
    organisms: List[str] = field(default_factory=list)
    series_supplementary_files: List[str] = field(default_factory=list)
    samples: List[Sample] = field(default_factory=list)

    @property
    def n_samples(self) -> int:
        return len(self.samples)

    @property
    def all_supplementary_files(self) -> List[str]:
        files = list(self.series_supplementary_files)
        for s in self.samples:
            files.extend(s.supplementary_files)
        return files


def _split(line: str) -> tuple[str, str]:
    """Split a SOFT '!key = value' line into (key, value)."""
    key, _, value = line.partition("=")
    return key.strip(), value.strip()


def _basename(path: str) -> str:
    return os.path.basename(path.rstrip("/"))


def parse_soft(text: str) -> GeoMetadata:
    """Parse combined SOFT text (series + samples) into a GeoMetadata object."""
    meta = GeoMetadata()
    current: Sample | None = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line:
            continue

        if line.startswith("^SERIES"):
            _, val = _split(line)
            meta.accession = val
            current = None
            continue
        if line.startswith("^PLATFORM"):
            current = None
            continue
        if line.startswith("^SAMPLE"):
            _, gsm = _split(line)
            current = Sample(gsm=gsm)
            meta.samples.append(current)
            continue
        if not line.startswith("!"):
            continue

        key, val = _split(line)

        # --- Series-level fields ---
        if current is None:
            if key == "!Series_title":
                meta.title = val
            elif key == "!Series_summary":
                meta.summary = (meta.summary + " " + val).strip()
            elif key == "!Series_overall_design":
                meta.overall_design = val
            elif key == "!Series_type":
                meta.series_type = (meta.series_type + "; " + val).strip("; ") if meta.series_type else val
            elif key == "!Series_supplementary_file":
                meta.series_supplementary_files.append(_basename(val))
            elif key in ("!Series_platform_id",):
                meta.platform_id = val
            elif key == "!Platform_title":
                meta.platform_title = val
            continue

        # --- Sample-level fields ---
        if key == "!Sample_title":
            current.title = val
        elif key == "!Sample_source_name_ch1":
            current.source_name = val
        elif key == "!Sample_organism_ch1":
            current.organism = val
            if val and val not in meta.organisms:
                meta.organisms.append(val)
        elif key == "!Sample_library_strategy":
            current.library_strategy = val
        elif key == "!Sample_characteristics_ch1":
            ckey, sep, cval = val.partition(":")
            if sep:
                ckey = ckey.strip().lower()
                cval = cval.strip()
                if ckey in current.characteristics and current.characteristics[ckey] != cval:
                    current.extra_characteristics.append(f"{ckey}: {cval}")
                else:
                    current.characteristics[ckey] = cval
            else:
                current.extra_characteristics.append(val)
        elif re.match(r"!Sample_supplementary_file(_\d+)?$", key):
            if val and val.lower() != "none":
                current.supplementary_files.append(_basename(val))

    if not meta.platform_title and meta.platform_id:
        meta.platform_title = meta.platform_id
    return meta
