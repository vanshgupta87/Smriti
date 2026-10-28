"""
Smriti: HL7 FHIR R4 ServiceRequest Generator & CDS Hooks Protocol
Creates standardized JSON resources compliant with Epic/Cerner EHR specifications.
"""
import uuid
from datetime import datetime

def create_fhir_servicerequest(patient_id: str, patient_name: str, mrn: str, modality: str, rationale: str):
    return {
        "resourceType": "ServiceRequest",
        "id": f"sr-{uuid.uuid4().hex[:8]}",
        "status": "active",
        "intent": "order",
        "priority": "urgent",
        "subject": {
            "reference": f"Patient/{patient_id}",
            "display": patient_name,
            "identifier": {"system": "urn:oid:hospital-mrn", "value": mrn}
        },
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "24627-2" if "MRI" in modality else "98766-2",
                "display": f"Order {modality} diagnostic protocol"
            }]
        },
        "reasonCode": [{"text": rationale}],
        "authoredOn": datetime.utcnow().isoformat() + "Z"
    }
