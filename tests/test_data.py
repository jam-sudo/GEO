from pathlib import Path

import pytest

from geo_portfolio import data
from geo_portfolio.data import DataDownloadError, download_counts, raw_count_urls
from geo_portfolio.parse import parse_soft


def test_raw_count_urls_prefers_gene_level(soft_157830):
    meta = parse_soft(soft_157830)
    urls = raw_count_urls(meta)
    assert urls, "expected a raw-count URL for GSE157830"
    assert all("genes.counts" in u for u in urls)          # gene-level only
    assert not any("isoform" in u for u in urls)
    assert all(u.startswith("https://") for u in urls)      # ftp -> https


def test_raw_count_urls_none_for_fpkm_only(soft_78220):
    assert raw_count_urls(parse_soft(soft_78220)) == []


def test_raw_count_urls_none_for_microarray(soft_2034):
    assert raw_count_urls(parse_soft(soft_2034)) == []


def test_download_counts_writes_files(soft_157830, tmp_path, monkeypatch):
    # mock the actual HTTP download
    def fake_download(url, dest, timeout=120):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"fake-gzip")
        return dest
    monkeypatch.setattr(data, "_download", fake_download)

    meta = parse_soft(soft_157830)
    paths = download_counts(meta, tmp_path)
    assert paths
    for p in paths:
        assert Path(p).exists()
        assert Path(p).parent == tmp_path / "data" / "raw"


def test_download_counts_raises_when_none(soft_2034, tmp_path):
    with pytest.raises(DataDownloadError):
        download_counts(parse_soft(soft_2034), tmp_path)
