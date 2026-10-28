import io
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from PIL import Image
from fastapi import UploadFile

import backend.app as app_module


class MLPAndTumorTests(unittest.TestCase):
    def test_mlp_models_present_in_stage_status(self):
        statuses = app_module.triage_stage_status()["stages"]
        self.assertEqual(len(statuses), 4)
        for stage in statuses:
            self.assertIn("mlp_loaded", stage)
            self.assertIn("mlp_threshold_loaded", stage)

    def test_mlp_prediction_generation(self):
        # Verify predict_triage returns mlp_prediction when stage model is loaded
        req = app_module.DynamicTriageRequest(
            stage=1,
            patient_id=None,
            cognitive={"adas13": 15.0, "mmse": 26.0, "cdr_sob": 1.5, "faq": 2.0, "moca": 24.0},
        )
        if 1 in app_module.MODELS and 1 in app_module.MLP_MODELS:
            res = app_module.predict_triage(req)
            self.assertIn("calibrated_risk", res)
            self.assertIn("mlp_prediction", res)
            if res["mlp_prediction"] is not None:
                self.assertIn("progression_24m_risk", res["mlp_prediction"])
                self.assertIn("optimal_threshold", res["mlp_prediction"])
                self.assertIn("model_comparison", res)

    def test_tumor_detection_validation(self):
        import asyncio

        # Test invalid extension
        fake_file = UploadFile(filename="scan.txt", file=io.BytesIO(b"dummy data"))
        with self.assertRaises(app_module.HTTPException) as ctx:
            asyncio.run(app_module.detect_brain_tumor(file=fake_file, model_variant="nano"))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_tumor_detection_valid_image(self):
        import asyncio

        # Create a small valid test image (64x64 RGB)
        img = Image.new("RGB", (64, 64), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        fake_file = UploadFile(filename="scan.png", file=buf)
        res = asyncio.run(app_module.detect_brain_tumor(file=fake_file, model_variant="nano"))
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["model_variant"], "nano")
        self.assertIn("detections", res)
        self.assertIn("research_notice", res)


if __name__ == "__main__":
    unittest.main()
