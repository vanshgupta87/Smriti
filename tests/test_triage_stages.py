from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np
from fastapi import HTTPException

import backend.app as app_module


class CapturingModel:
    def __init__(self) -> None:
        self.features = None

    def predict_proba(self, features):
        self.features = features.copy()
        return np.asarray([[0.4, 0.6]])

    def get_booster(self):
        return CapturingBooster()


class CapturingBooster:
    def predict(self, _matrix, pred_contribs: bool = False):
        return np.asarray([[0.1, 0.2, 0.3, 0.4, 0.0]])


class FixedCalibrator:
    def predict(self, probabilities):
        return np.asarray([0.5])


class TriageStageTests(unittest.TestCase):
    def test_stage_status_marks_missing_artifacts_unavailable(self) -> None:
        with (
            patch.object(app_module, "MODELS", {}),
            patch.object(app_module, "CALIBRATORS", {}),
            patch.object(app_module, "STAGE_THRESHOLDS", {}),
        ):
            statuses = app_module.triage_stage_status()["stages"]

        self.assertEqual(len(statuses), 4)
        self.assertTrue(all(not stage["model_loaded"] for stage in statuses))
        self.assertTrue(all(stage["error"] for stage in statuses))

    def test_missing_model_returns_service_unavailable(self) -> None:
        request = app_module.DynamicTriageRequest(stage=2, cognitive={})
        with patch.object(app_module, "MODELS", {}):
            with self.assertRaises(HTTPException) as raised:
                app_module.predict_triage(request)

        self.assertEqual(raised.exception.status_code, 503)

    def test_stage2_passes_standardized_scores_without_conversion(self) -> None:
        feature_names = [
            "composite_ptau217_z",
            "composite_abeta_ratio_z",
            "upenn_NfL_Q_z",
            "upenn_GFAP_Q_z",
        ]
        model = CapturingModel()
        request = app_module.DynamicTriageRequest(
            stage=2,
            patient_id=None,
            cognitive={},
            plasma_ptau217_z=0.25,
            plasma_ab42_40_z=-0.5,
            plasma_nfl_z=1.25,
            plasma_gfap_z=-1.0,
        )
        with (
            patch.object(app_module, "MODELS", {2: model}),
            patch.object(app_module, "FEATURE_LISTS", {2: feature_names}),
            patch.object(app_module, "CALIBRATORS", {2: FixedCalibrator()}),
            patch.object(app_module, "STAGE_THRESHOLDS", {2: 0.4}),
            patch.object(app_module.xgb, "DMatrix", return_value=object()),
        ):
            result = app_module.predict_triage(request)

        self.assertEqual(
            model.features.iloc[0].tolist(),
            [0.25, -0.5, 1.25, -1.0],
        )
        self.assertEqual(result["stage"], 2)
        self.assertEqual(result["calibrated_risk"], 0.5)

    def test_stage2_requires_at_least_one_measured_biomarker(self) -> None:
        request = app_module.DynamicTriageRequest(
            stage=2,
            patient_id=None,
            cognitive={},
        )
        with patch.object(app_module, "MODELS", {2: object()}):
            with self.assertRaises(HTTPException) as raised:
                app_module.predict_triage(request)

        self.assertEqual(raised.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
