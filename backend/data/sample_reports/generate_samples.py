import os
from pathlib import Path

out_dir = Path(__file__).parent

# Sample 1: Eleanor Rostova (Stage 4 Candidate)
eleanor_report = """QUEST DIAGNOSTICS - CLINICAL NEURO-BIOMARKER & COGNITIVE SUMMARY
Patient Name: Eleanor K. Rostova
MRN: ADNI-002-S-0413
Age: 74
Gender: Female
Education Years: 16
APOE Genotype: e4/e4

CLINICAL ASSESSMENTS:
MMSE Score: 18.0
MoCA Score: 14.0
CDR-SB Total: 7.5
FAQ Total: 18.0
ADAS-13: 32.5
GDS-15: 4.0

PLASMA PROTEOMICS (Simoa HD-X):
p-tau217: 0.48 pg/mL (High Risk Reference > 0.38)
Ab42/Ab40: 0.052 (Abnormal Reference < 0.065)
NfL: 38.5 pg/mL
GFAP: 320.0 pg/mL

VOLUMETRIC 3D MRI (FreeSurfer v7.4):
Hippocampus Volume: 2.85 cm3
Ventricles Volume: 48.2 cm3
WMH Volume: 6.4 cm3
MTA Grade: 3

MOLECULAR AMYLOID PET (GAAIN Standard):
Centiloids: 78.4 CL (Amyloid Positive Threshold >= 20.0)
Tau SUVR: 1.62
Cerebral Microbleeds: 1
"""

# Sample 2: John Mitchell (Stage 2 MCI)
john_report = """GE HEALTHCARE PRECISION MEDICINE - LAB WORKUP
Patient Name: John D. Mitchell
MRN: ADNI-002-S-0685
Age: 68
Gender: Male
Education Years: 14
APOE Genotype: e3/e4

CLINICAL ASSESSMENTS:
MMSE Score: 23.0
MoCA Score: 20.0
CDR-SB Total: 3.5
FAQ Total: 8.0
ADAS-13: 19.0
GDS-15: 3.0

PLASMA PROTEOMICS:
p-tau217: 0.32 pg/mL
Ab42/Ab40: 0.061
NfL: 22.0 pg/mL
GFAP: 195.0 pg/mL

VOLUMETRIC 3D MRI:
Hippocampus Volume: 3.40 cm3
Ventricles Volume: 36.0 cm3
WMH Volume: 3.8 cm3
MTA Grade: 2

MOLECULAR AMYLOID PET:
Centiloids: 34.0 CL
Tau SUVR: 1.25
Cerebral Microbleeds: 0
"""

# Sample 3: Sarah Jenkins (Reversible Mimic / Normal Biomarkers)
sarah_report = """LABCORP NEUROLOGICAL ASSESSMENT REPORT
Patient Name: Sarah Jenkins
MRN: ADNI-003-S-1024
Age: 62
Gender: Female
Education Years: 18
APOE Genotype: e3/e3

CLINICAL ASSESSMENTS:
MMSE Score: 28.0
MoCA Score: 26.0
CDR-SB Total: 0.5
FAQ Total: 1.0
ADAS-13: 8.0
GDS-15: 2.0

PLASMA PROTEOMICS:
p-tau217: 0.12 pg/mL (Normal Reference < 0.22)
Ab42/Ab40: 0.092 (Normal Reference > 0.075)
NfL: 11.5 pg/mL
GFAP: 110.0 pg/mL

VOLUMETRIC 3D MRI:
Hippocampus Volume: 4.10 cm3
Ventricles Volume: 24.0 cm3
WMH Volume: 1.2 cm3
MTA Grade: 0

MOLECULAR AMYLOID PET:
Centiloids: 8.5 CL (Amyloid Negative)
Tau SUVR: 1.04
Cerebral Microbleeds: 0
"""

def create_simple_pdf(filename: str, text: str):
    lines = text.strip().split("\n")
    stream_content = "BT\n/F1 10 Tf\n20 770 Td\n14 TL\n"
    for line in lines:
        clean_line = line.encode("ascii", "replace").decode("ascii")
        escaped = clean_line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_content += f"({escaped}) '\n"
    stream_content += "ET"
    
    stream_bytes = stream_content.encode("ascii")
    length = len(stream_bytes)
    
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(length).encode("ascii") + b" >>\nstream\n"
        + stream_bytes +
        b"\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000244 00000 n \n"
        + str(244 + length + 30).zfill(10).encode("ascii") + b" 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(244 + length + 110).encode("ascii") + b"\n%%EOF"
    )
    
    with open(out_dir / filename, "wb") as f:
        f.write(pdf_content)
    with open(out_dir / filename.replace(".pdf", ".txt"), "w") as f:
        f.write(text)

create_simple_pdf("Quest_Biomarkers_EleanorRostova.pdf", eleanor_report)
create_simple_pdf("GE_Precision_Cognitive_Lab_JohnMitchell.pdf", john_report)
create_simple_pdf("Laborp_Neuro_Workup_SarahJenkins.pdf", sarah_report)
print("Successfully generated sample PDF and text reports!")
