import re
from pathlib import Path

import pandas as pd


def canonicalize_disease(label: str) -> str:
    """Map a WHO indicator disease label to a canonical disease name.

    Heuristic rules focus on common outbreak-relevant diseases.
    Returns empty string when no confident match, to allow manual curation.
    """
    if not isinstance(label, str):
        return ""

    text = label.lower()
    # Normalize punctuation and spaces
    text = re.sub(r"[\-/_,]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Ordered checks by specificity
    if any(k in text for k in ["covid", "coronavirus", "sars cov", "sars-cov-2", "sars cov 2"]):
        return "Covid-19"
    if any(k in text for k in ["mpox", "monkeypox"]):
        return "Mpox"
    if "lassa" in text:
        return "Lassa Fever"
    if any(k in text for k in ["yellow fever", "y f", "y.f"]):
        return "Yellow Fever"
    if "cholera" in text:
        return "Cholera"
    if "measles" in text:
        return "Measles"
    if any(k in text for k in ["meningitis", "cerebrospinal meningitis", "cs m", "csm"]):
        return "Meningitis"
    if "diphtheria" in text:
        return "Diphtheria"
    if "malaria" in text:
        return "Malaria"
    if any(k in text for k in ["polio", "acute flaccid paralysis", "afp"]):
        # Most AFP metrics relate to polio surveillance
        return "Polio"
    if "influenza" in text:
        return "Influenza"
    if "rabies" in text:
        return "Rabies"
    if any(k in text for k in ["tuberculosis", "tb cases"]):
        return "Tuberculosis"
    if "hepatitis" in text:
        return "Hepatitis"
    if any(k in text for k in ["typhoid", "enteric fever"]):
        return "Typhoid Fever"
    if "dengue" in text:
        return "Dengue"
    if "ebola" in text:
        return "Ebola"
    if "pertussis" in text or "whooping cough" in text:
        return "Pertussis"
    if "rotavirus" in text:
        return "Rotavirus"

    # No confident match
    return ""


def main():
    root = Path(__file__).parent
    who_raw = root / "data" / "raw" / "who_disease_data.csv"
    mapping_out = root / "data" / "raw" / "who_indicator_mapping.csv"

    if not who_raw.exists():
        print(f"[ERROR] Missing WHO raw file: {who_raw}")
        return

    df = pd.read_csv(who_raw)
    # Expect columns like: disease_label, indicator_code (and others), but be defensive
    # Create pairs of (disease_label, indicator_code)
    label_col = "disease_label" if "disease_label" in df.columns else None
    code_col = "indicator_code" if "indicator_code" in df.columns else None

    if not label_col or not code_col:
        # Try alternatives if structure differs
        possible_label_cols = [c for c in df.columns if "label" in c.lower() or "disease" in c.lower()]
        possible_code_cols = [c for c in df.columns if "indicator" in c.lower() or "code" in c.lower()]
        if possible_label_cols:
            label_col = possible_label_cols[0]
        if possible_code_cols:
            code_col = possible_code_cols[0]

    if not label_col or not code_col:
        print("[ERROR] Could not find label and code columns in WHO data.")
        print(f"Columns present: {list(df.columns)}")
        return

    pairs = (
        df[[label_col, code_col]]
        .dropna()
        .drop_duplicates()
        .rename(columns={label_col: "disease_label", code_col: "indicator_code"})
    )

    pairs["canonical_disease"] = pairs["disease_label"].apply(canonicalize_disease)

    # Sort for stable output
    pairs = pairs.sort_values(["canonical_disease", "disease_label", "indicator_code"], na_position="last")

    # Ensure directory exists
    mapping_out.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(mapping_out, index=False)
    print(f"[SAVED] {mapping_out} rows={len(pairs)}")


if __name__ == "__main__":
    main()