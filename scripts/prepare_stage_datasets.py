#!/usr/bin/env python3
"""Validate the supplied stage CSVs and materialize training Parquet files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_DIR / "Dataset" / "Dataset"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
STAGE_DATASETS = (
    (1, "screening", "stage1_screening.parquet", ()),
    (2, "plasma", "stage2_plasma.parquet", (
        "composite_ptau217_z",
        "composite_abeta_ratio_z",
        "upenn_NfL_Q_z",
        "upenn_GFAP_Q_z",
    )),
    (3, "mri", "stage3_mri.parquet", (
        "hippocampus_icv_ratio",
        "ventricles_icv_ratio",
        "wmh_volume_cm3",
    )),
    (4, "pet", "stage4_pet.parquet", (
        "Amyloid_Centiloids",
        "Tau_MetaTemporal_SUVR",
    )),
)
REQUIRED_COLUMNS = {"PTID", "VISCODE2", "VISDATE", "Progression24m"}
def prepare_stage(stage: int, source_name: str, output_name: str, modality_columns: tuple[str, ...]) -> None:
    source_path = SOURCE_DIR / f"part{stage}_{source_name}.csv"
    if not source_path.is_file():
        raise FileNotFoundError(
            f"Missing supplied stage dataset: {source_path}. "
            "Provide the matching partN_*.csv file before training."
        )

    frame = pd.read_csv(source_path, low_memory=False)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"{source_path.name} is missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError(f"{source_path.name} contains no observations.")

    frame["PTID"] = frame["PTID"].astype("string").str.strip()
    frame["VISCODE2"] = frame["VISCODE2"].astype("string").str.strip().str.lower()
    frame["VISDATE"] = pd.to_datetime(frame["VISDATE"], errors="coerce")
    frame["Progression24m"] = pd.to_numeric(frame["Progression24m"], errors="coerce")
    if frame[["PTID", "VISCODE2", "VISDATE", "Progression24m"]].isna().any().any():
        raise ValueError(f"{source_path.name} has missing patient/visit/date/target values.")
    if not frame["Progression24m"].isin((0, 1)).all():
        raise ValueError(f"{source_path.name} progression targets must be binary (0 or 1).")
    if frame.duplicated(["PTID", "VISCODE2"]).any():
        raise ValueError(f"{source_path.name} has duplicate patient/visit rows.")
    if frame["PTID"].nunique() < 20 or frame["Progression24m"].nunique() != 2:
        raise ValueError(
            f"{source_path.name} must have at least 20 patients and both target classes."
        )

    if modality_columns:
        available = [
            column for column in modality_columns
            if column in frame and frame[column].notna().any()
        ]
        if not available:
            raise ValueError(
                f"{source_path.name} has no populated stage-specific modality columns "
                f"from {list(modality_columns)}."
            )
        patients_with_modality = frame.loc[
            :, available
        ].notna().any(axis=1).groupby(frame["PTID"]).any().sum()
        if patients_with_modality < 20:
            raise ValueError(
                f"{source_path.name} has stage-specific measurements for only "
                f"{patients_with_modality} patients; at least 20 are required."
            )

    output_path = OUTPUT_DIR / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)
    print(
        f"Stage {stage}: {len(frame)} visits / {frame['PTID'].nunique()} patients; "
        f"{int(frame['Progression24m'].sum())} positive targets; saved {output_path}"
    )


def main() -> None:
    for stage_spec in STAGE_DATASETS:
        prepare_stage(*stage_spec)
    print("All four supplied stage datasets validated and prepared.")


if __name__ == "__main__":
    main()
