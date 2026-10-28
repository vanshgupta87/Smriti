"""
Smriti: LASI-DAD Demographic Fairness & Recalibration Layer
Adjusts cognitive scores for low formal literacy in South Asian elders and adjusts metabolic risk.
"""
def apply_lasidad_hcap_offset(raw_score: float, education_years: float, test_type: str = "MMSE") -> float:
    if education_years >= 12.0:
        return raw_score
    deficit = 12.0 - max(0.0, education_years)
    rate = 0.35 if test_type == "MMSE" else 0.45
    return min(30.0, raw_score + (deficit * rate))
