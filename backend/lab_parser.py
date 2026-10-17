"""
StepWise PRO: Clinical Lab PDF & EHR Report Parser
Zero-dependency, high-speed pure-Python text and PDF stream parser.
"""

import re
import zlib
from typing import Dict, Any, Optional

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts raw text strings from PDF binary bytes including FlateDecode streams."""
    extracted_text = []
    
    # 1. Look for uncompressed text in parentheses: (Sample Text) Tj or [(S)(a)(m)(p)(l)(e)] TJ
    simple_matches = re.findall(rb'\(([^()]{2,100})\)\s*T[jJ]', pdf_bytes)
    for m in simple_matches:
        try:
            extracted_text.append(m.decode('utf-8', errors='ignore'))
        except Exception:
            pass
            
    # 2. Look for compressed streams (FlateDecode)
    stream_pattern = re.compile(rb'stream[\r\n]+(.*?)[\r\n]+endstream', re.DOTALL)
    for stream_match in stream_pattern.finditer(pdf_bytes):
        raw_stream = stream_match.group(1)
        try:
            decompressed = zlib.decompress(raw_stream)
            # Find strings in decompressed stream
            stream_strings = re.findall(rb'\(([^()]{2,100})\)\s*T[jJ]', decompressed)
            for s in stream_strings:
                try:
                    extracted_text.append(s.decode('utf-8', errors='ignore'))
                except Exception:
                    pass
            # Also search for plain text chunks in decompressed stream
            clean_stream = re.sub(rb'[^a-zA-Z0-9\.\:\-\_\,\s\/]', b' ', decompressed)
            extracted_text.append(clean_stream.decode('utf-8', errors='ignore'))
        except Exception:
            # Not a zlib stream or corrupt; ignore
            pass
            
    # 3. Fallback: Search all ASCII strings if little text found
    if len(extracted_text) < 5:
        ascii_matches = re.findall(rb'[a-zA-Z0-9\.\:\-\_\,\s\/]{4,}', pdf_bytes)
        for a in ascii_matches:
            extracted_text.append(a.decode('utf-8', errors='ignore'))
            
    return "\n".join(extracted_text)


def parse_clinical_report_text(text: str) -> Dict[str, Any]:
    """Parses extracted clinical text into structured biomarker, cognitive, and patient parameters."""
    result: Dict[str, Any] = {
        "patient_name": None,
        "mrn": None,
        "age": None,
        "gender": None,
        "education_years": None,
        "apoe": None,
        "apoe4_count": None,
        "cognitive": {},
        "plasma": {},
        "mri": {},
        "pet": {},
        "raw_matches": []
    }
    
    # 1. Patient Demographics
    name_match = re.search(r'(?:Patient Name|Name|Patient):\s*([A-Za-z\s\.\,\-]+?)(?:\n|\r|\t|MRN|DOB|Age|$)', text, re.IGNORECASE)
    if name_match:
        result["patient_name"] = name_match.group(1).strip()
        
    mrn_match = re.search(r'(?:MRN|Patient ID|ID):\s*([A-Za-z0-9\-]+)', text, re.IGNORECASE)
    if mrn_match:
        result["mrn"] = mrn_match.group(1).strip()
        
    age_match = re.search(r'(?:Age|AGE):\s*(\d{2,3})', text, re.IGNORECASE)
    if age_match:
        result["age"] = float(age_match.group(1))
        
    gender_match = re.search(r'(?:Gender|Sex):\s*(Female|Male|F|M)', text, re.IGNORECASE)
    if gender_match:
        g = gender_match.group(1).upper()
        result["gender"] = "Female" if g in ["F", "FEMALE"] else "Male"
        
    edu_match = re.search(r'(?:Education|Edu(?:cation)?\s*Years?):\s*(\d{1,2})', text, re.IGNORECASE)
    if edu_match:
        result["education_years"] = float(edu_match.group(1))
        
    # 2. Genetics (APOE)
    apoe_match = re.search(r'APOE\s*(?:Genotype|status)?[:\s]*([εeE][234]\s*\/\s*[εeE][234]|\d\/\d)', text, re.IGNORECASE)
    if apoe_match:
        apoe_str = apoe_match.group(1).replace('e', 'ε').replace('E', 'ε')
        result["apoe"] = apoe_str
        result["apoe4_count"] = apoe_str.count('4')
        result["raw_matches"].append({"field": "APOE", "value": apoe_str, "confidence": 0.98})

    # 3. Cognitive Battery
    cognitive_patterns = [
        ("mmse", r'MMSE(?:\s*Score|\s*Total)?[:\s]*(\d{1,2}(?:\.\d+)?)'),
        ("moca", r'MoCA(?:\s*Score|\s*Total)?[:\s]*(\d{1,2}(?:\.\d+)?)'),
        ("cdrsb", r'CDR(?:-|\s*)SB(?:\s*Total)?[:\s]*(\d{1,2}(?:\.\d+)?)'),
        ("faq", r'FAQ(?:\s*Total)?[:\s]*(\d{1,2}(?:\.\d+)?)'),
        ("adas13", r'ADAS(?:-|\s*)13[:\s]*(\d{1,2}(?:\.\d+)?)'),
        ("gds", r'GDS(?:-15)?[:\s]*(\d{1,2}(?:\.\d+)?)'),
    ]
    for key, pat in cognitive_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            result["cognitive"][key] = val
            result["raw_matches"].append({"field": key.upper(), "value": val, "confidence": 0.95})

    # 4. Biofluid Blood Biomarkers
    plasma_patterns = [
        ("plasma_ptau217", r'p(?:-|\s*)tau\s*217[:\s]*(\d+(?:\.\d+)?)\s*(?:pg\/mL)?'),
        ("plasma_ab42_40", r'(?:Aβ42\/Aβ40|AB42\/AB40|Abeta\s*42\/40|AB42_40)[:\s]*(\d+(?:\.\d+)?)'),
        ("plasma_nfl", r'(?:Plasma\s*)?NfL[:\s]*(\d+(?:\.\d+)?)\s*(?:pg\/mL)?'),
        ("plasma_gfap", r'(?:Plasma\s*)?GFAP[:\s]*(\d+(?:\.\d+)?)\s*(?:pg\/mL)?'),
    ]
    for key, pat in plasma_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            result["plasma"][key] = val
            result["raw_matches"].append({"field": key, "value": val, "confidence": 0.96})

    # 5. MRI Volumetry
    mri_patterns = [
        ("hippocampus_cm3", r'Hippocamp(?:us|al)\s*(?:Volume)?[:\s]*(\d+(?:\.\d+)?)\s*(?:cm3|mL)?'),
        ("ventricles_cm3", r'Ventric(?:les|ular)\s*(?:Volume)?[:\s]*(\d+(?:\.\d+)?)\s*(?:cm3|mL)?'),
        ("wmh_volume_cm3", r'WMH\s*(?:Volume)?[:\s]*(\d+(?:\.\d+)?)\s*(?:cm3|mL)?'),
        ("mta_grade", r'(?:Scheltens|MTA)\s*(?:Grade|Score)?[:\s]*([0-4]|Grade\s*[0-4])'),
    ]
    for key, pat in mri_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val_raw = m.group(1).strip()
            result["mri"][key] = float(val_raw) if key != "mta_grade" else val_raw
            result["raw_matches"].append({"field": key, "value": val_raw, "confidence": 0.92})

    # 6. PET Molecular
    pet_patterns = [
        ("centiloids", r'Centiloids?[:\s]*(\d+(?:\.\d+)?)\s*(?:CL)?'),
        ("tau_suvr", r'(?:MetaTemporal|Tau)\s*SUVR[:\s]*(\d+(?:\.\d+)?)'),
        ("microbleeds", r'(?:Cerebral\s*)?Microbleeds?[:\s]*(\d+)'),
    ]
    for key, pat in pet_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            result["pet"][key] = val
            result["raw_matches"].append({"field": key, "value": val, "confidence": 0.94})

    return result
