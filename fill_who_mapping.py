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
    # Yellow Fever: allow common abbreviations but avoid false positives like "anY First"
    if ("yellow fever" in text) or re.search(r"\bY[ .-]?F\b", text, flags=re.IGNORECASE):
        return "Yellow Fever"
    if "cholera" in text:
        return "Cholera"
    if "measles" in text:
        return "Measles"
    if "rubella" in text:
        return "Rubella"
    if "mumps" in text:
        return "Mumps"
    # Meningitis abbreviations (CSM) safely matched
    if ("meningitis" in text) or ("cerebrospinal meningitis" in text) or re.search(r"\bCS[ .-]?M\b", text, flags=re.IGNORECASE):
        return "Meningitis"
    if "diphtheria" in text:
        return "Diphtheria"
    if "malaria" in text:
        return "Malaria"
    if any(k in text for k in ["japanese encephalitis", "encephalitis japanese"]):
        return "Japanese Encephalitis"
    if any(k in text for k in ["polio", "acute flaccid paralysis", "afp"]):
        # Most AFP metrics relate to polio surveillance
        return "Polio"
    if "influenza" in text:
        return "Influenza"
    if "rabies" in text:
        return "Rabies"
    if any(k in text for k in ["tuberculosis", "tb cases", "mdr tb", "xdr tb", "rr tb", "tb "]):
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
    if any(k in text for k in ["trypanosomiasis", "sleeping sickness", "gambiense", "rhodesiense"]):
        return "Trypanosomiasis"
    if "rotavirus" in text:
        return "Rotavirus"
    if "neonatal tetanus" in text or "tetanus" in text:
        return "Tetanus"
    if "leishmaniasis" in text or "leish" in text:
        return "Leishmaniasis"
    if "buruli" in text:
        return "Buruli Ulcer"
    if "yaws" in text:
        return "Yaws"
    if "leprosy" in text:
        return "Leprosy"

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

    # Fill remaining blanks using indicator_code heuristics
    if "indicator_code" in pairs.columns:
        # TB prefixed codes are tuberculosis
        mask_tb = (pairs["canonical_disease"].astype(str).str.strip() == "") & pairs["indicator_code"].astype(str).str.upper().str.startswith("TB_")
        pairs.loc[mask_tb, "canonical_disease"] = "Tuberculosis"
        # NTD_4 is human African trypanosomiasis
        mask_hat = (pairs["canonical_disease"].astype(str).str.strip() == "") & (pairs["indicator_code"].astype(str).str.upper() == "NTD_4")
        pairs.loc[mask_hat, "canonical_disease"] = "Trypanosomiasis"

    # Sort for stable output
    pairs = pairs.sort_values(["canonical_disease", "disease_label", "indicator_code"], na_position="last")

    # Ensure directory exists
    mapping_out.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(mapping_out, index=False)
    print(f"[SAVED] {mapping_out} rows={len(pairs)}")


if __name__ == "__main__":
    main()