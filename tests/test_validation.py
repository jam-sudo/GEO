from geo_portfolio.fetch import validate_accession


def test_valid_accessions():
    assert validate_accession("GSE157830")
    assert validate_accession("GSE1")


def test_invalid_accessions():
    for bad in ["", "gse157830", "GSM12345", "GPL96", "GSE", "GSE12a", "12345", "GSE 1", None]:
        assert not validate_accession(bad)
