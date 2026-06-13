from pathlib import Path

import pytest
from typer.testing import CliRunner

from geo_portfolio import cli
from tests.conftest import load_soft

runner = CliRunner()


@pytest.fixture
def fake_fetch(monkeypatch):
    """Replace network fetch with fixture loading."""
    def _fake(accession, cache_dir=".geo_cache", refresh=False, timeout=60):
        return load_soft(accession)
    monkeypatch.setattr(cli, "fetch_soft", _fake)
    return _fake


def test_help_lists_commands():
    res = runner.invoke(cli.app, ["--help"])
    assert res.exit_code == 0
    for cmd in ["triage", "batch", "scaffold", "init-project", "run"]:
        assert cmd in res.output


def test_version():
    res = runner.invoke(cli.app, ["--version"])
    assert res.exit_code == 0
    assert "geo_portfolio" in res.output


def test_triage_invalid_accession_exit_2():
    res = runner.invoke(cli.app, ["triage", "not-an-accession"])
    assert res.exit_code == 2


def test_triage_writes_reports(fake_fetch, tmp_path):
    res = runner.invoke(cli.app, ["triage", "GSE157830", "--out", str(tmp_path),
                                  "--format", "markdown,json"])
    assert res.exit_code == 0, res.output
    assert "include" in res.output
    assert (tmp_path / "GSE157830_triage.md").exists()
    assert (tmp_path / "GSE157830_triage.json").exists()


def test_triage_microarray_reports_exclude(fake_fetch, tmp_path):
    res = runner.invoke(cli.app, ["triage", "GSE2034", "--out", str(tmp_path)])
    assert res.exit_code == 0
    assert "exclude" in res.output.lower()


def test_batch_continues_and_summarizes(fake_fetch, tmp_path):
    acc_file = tmp_path / "acc.txt"
    acc_file.write_text("# header\nGSE157830\nBADACC\nGSE2034\n")
    out = tmp_path / "reports"
    res = runner.invoke(cli.app, ["batch", str(acc_file), "--out", str(out)])
    assert res.exit_code == 0, res.output
    assert (out / "summary.csv").exists()
    assert (out / "summary.md").exists()
    summary = (out / "summary.csv").read_text()
    assert "GSE157830" in summary and "GSE2034" in summary
    # invalid accession recorded but did not abort the batch
    assert "BADACC" in summary
    assert (out / "GSE157830_triage.md").exists()


def test_scaffold_creates_project_from_template(tmp_path, monkeypatch):
    # run from the repo root so the template is found
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo_root)
    out = tmp_path / "GSE157830"
    res = runner.invoke(cli.app, ["scaffold", "GSE157830", "--out", str(out)])
    assert res.exit_code == 0, res.output
    assert (out / "analysis.qmd").exists()
    assert (out / "SUITABILITY.md").exists()
    assert (out / "results" / "figures").is_dir()
    # placeholder substituted
    assert "GSE157830" in (out / "analysis.qmd").read_text()
    assert "GSEXXXXXX" not in (out / "analysis.qmd").read_text()


def test_run_refuses_without_triage(tmp_path, monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo_root)
    out = tmp_path / "GSE157830"
    runner.invoke(cli.app, ["scaffold", "GSE157830", "--out", str(out)])
    # template SUITABILITY.md has empty decision -> run must refuse
    res = runner.invoke(cli.app, ["run", "GSE157830", "--project", str(out), "--dry-run"])
    assert res.exit_code == 1
    assert "Cannot run" in res.output or "decision" in res.output.lower()


@pytest.fixture
def no_network_download(monkeypatch):
    """Stub the count downloader so pipeline/data tests stay offline."""
    def _fake(meta, project_dir, overwrite=False, progress=None):
        p = Path(project_dir) / "data" / "raw" / "counts.txt.gz"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
        return [p]
    monkeypatch.setattr(cli, "download_counts", _fake)
    return _fake


def test_pipeline_excludes_stops(fake_fetch, no_network_download):
    res = runner.invoke(cli.app, ["pipeline", "GSE2034", "--yes"])
    assert res.exit_code == 1
    assert "Stopping" in res.output


def test_pipeline_scaffolds_and_guides_when_uncurated(fake_fetch, no_network_download, tmp_path, monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo_root)
    out = tmp_path / "GSE157830"
    res = runner.invoke(cli.app, ["pipeline", "GSE157830", "--out", str(out), "--yes"])
    assert res.exit_code == 0, res.output
    assert (out / "analysis.qmd").exists()
    assert (out / "SUITABILITY.md").exists()
    # scaffolded qmd is still the template -> pipeline must guide, not run
    assert "Next steps" in res.output


def test_pipeline_keeps_existing_project(fake_fetch, no_network_download, tmp_path, monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo_root)
    out = tmp_path / "GSE157830"
    out.mkdir()
    # contains the template marker (treated as uncurated) + a sentinel to detect overwrite
    (out / "analysis.qmd").write_text("# MY CUSTOM FILE\nSet the count-loading code for this dataset.\n")
    res = runner.invoke(cli.app, ["pipeline", "GSE157830", "--out", str(out), "--yes"])
    assert res.exit_code == 0, res.output
    # existing project preserved (not overwritten by the template)
    assert "MY CUSTOM FILE" in (out / "analysis.qmd").read_text()
    assert "keeping it" in res.output


def test_data_command(fake_fetch, no_network_download, tmp_path):
    res = runner.invoke(cli.app, ["data", "GSE157830", "--project", str(tmp_path)])
    assert res.exit_code == 0, res.output
    assert (tmp_path / "data" / "raw" / "counts.txt.gz").exists()
