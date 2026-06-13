from geo_portfolio.parse import parse_soft
from geo_portfolio.suitability import assess, classify_file, infer_factors


def test_classify_file():
    assert classify_file("GSE157830_genes.counts.txt.gz") == "raw_counts"
    assert classify_file("GSE60450_Lactation-GenewiseCounts.txt.gz") == "raw_counts"
    assert classify_file("study_htseq_counts.tsv") == "raw_counts"
    assert classify_file("GSE78220_PatientFPKM.xlsx") == "fpkm"
    assert classify_file("sample_TPM.txt") == "tpm"
    assert classify_file("expr_RPKM.csv") == "rpkm"
    assert classify_file("normalized_matrix.txt") == "normalized"
    assert classify_file("GSE2034_RAW.tar") == "archive"
    assert classify_file("GSM123.CEL.gz") == "microarray_raw"
    assert classify_file("readme.txt") == "other"


def test_raw_counts_rnaseq_is_suitable(soft_157830):
    suit = assess(parse_soft(soft_157830))
    assert suit.assay == "rna_seq"
    assert suit.raw_counts_available == "yes"
    assert suit.suitability_class == "suitable"
    assert suit.decision == "include"
    assert suit.de_method == "DESeq2"


def test_microarray_is_unsuitable(soft_2034):
    suit = assess(parse_soft(soft_2034))
    assert suit.assay == "microarray"
    assert suit.suitability_class == "unsuitable"
    assert suit.decision == "exclude"
    assert "limma" in suit.de_method.lower()
    assert any("microarray" in w.lower() for w in suit.warnings)


def test_fpkm_only_is_conditional(soft_78220):
    suit = assess(parse_soft(soft_78220))
    assert suit.assay == "rna_seq"
    assert suit.raw_counts_available == "no"
    assert suit.normalized_values_present == "yes"
    assert suit.suitability_class == "manual_review"
    assert suit.decision == "conditional"
    assert any("fpkm" in w.lower() or "normalized" in w.lower() for w in suit.warnings)


def test_ambiguous_metadata_flagged(soft_ambiguous):
    meta = parse_soft(soft_ambiguous)
    factors = infer_factors(meta.samples)
    # the only characteristic (patient id) is unique per sample -> ambiguous
    assert factors and all(f.ambiguous for f in factors)
    suit = assess(meta)
    # raw counts present but no usable grouping -> manual review, not include
    assert suit.suitability_class == "manual_review"
    assert suit.metadata_clarity in ("messy", "unknown")
    assert any("ambiguous" in w.lower() or "curation" in w.lower() for w in suit.warnings)


def test_score_is_bounded_and_explained(soft_157830):
    suit = assess(parse_soft(soft_157830))
    assert 0 <= suit.score <= 100
    assert suit.reasons and all("text" in r and "delta" in r for r in suit.reasons)
