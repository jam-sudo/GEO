from geo_portfolio.parse import parse_soft


def test_parse_series_fields(soft_157830):
    meta = parse_soft(soft_157830)
    assert meta.accession == "GSE157830"
    assert "Ferroptosis" in meta.title
    assert meta.organisms == ["Homo sapiens"]
    assert "high throughput sequencing" in meta.series_type.lower()


def test_parse_samples_and_characteristics(soft_157830):
    meta = parse_soft(soft_157830)
    assert meta.n_samples == 12
    s0 = meta.samples[0]
    assert s0.gsm.startswith("GSM")
    assert s0.library_strategy.lower() == "rna-seq"
    # characteristics parsed as key->value
    assert "genotype/variation" in s0.characteristics
    assert s0.characteristics["cell line"].lower() in ("tu8902", "miapaca2")


def test_parse_supplementary_files(soft_157830):
    meta = parse_soft(soft_157830)
    files = " ".join(meta.all_supplementary_files).lower()
    assert "genes.counts.txt.gz" in files
    assert "fpkm" in files


def test_parse_microarray(soft_2034):
    meta = parse_soft(soft_2034)
    assert "by array" in meta.series_type.lower()
