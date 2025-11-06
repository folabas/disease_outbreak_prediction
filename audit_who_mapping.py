from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


ROOT = Path(__file__).parent
RAW_DIR = ROOT / "data" / "raw"
MAP_PATH = RAW_DIR / "who_indicator_mapping.csv"
WHO_WEEKLY_PATH = RAW_DIR / "who_disease_data_weekly.csv"


def suggest_canonical(label: str) -> Optional[str]:
    if not isinstance(label, str):
        return None
    l = label.strip().lower()
    # Strip common suffixes like "cases", "deaths"
    l = l.replace("cases", "").replace("deaths", "").strip()
    # Heuristic mappings for common outbreak diseases
    if any(k in l for k in ["covid", "coronavirus", "sars-cov"]):
        return "Covid-19"
    if "lassa" in l:
        return "Lassa Fever"
    if any(k in l for k in ["yellow", "y.f", "yf"]):
        return "Yellow Fever"
    if any(k in l for k in ["mening", "csm", "cerebrospinal"]):
        return "Meningitis"
    if "cholera" in l:
        return "Cholera"
    if any(k in l for k in ["mpox", "monkeypox"]):
        return "Mpox"
    if "measles" in l:
        return "Measles"
    if "dengue" in l:
        return "Dengue"
    if "malaria" in l:
        return "Malaria"
    if "polio" in l:
        return "Polio"
    if "typhoid" in l:
        return "Typhoid"
    if any(k in l for k in ["influenza", "flu"]):
        return "Influenza"
    if "hepatitis a" in l:
        return "Hepatitis A"
    if "hepatitis b" in l:
        return "Hepatitis B"
    if "hepatitis e" in l:
        return "Hepatitis E"
    if "diphtheria" in l:
        return "Diphtheria"
    if "pertussis" in l or "whooping" in l:
        return "Pertussis"
    if "rabies" in l:
        return "Rabies"
    if "rotavirus" in l:
        return "Rotavirus"
    if "ebola" in l:
        return "Ebola"
    if "norovirus" in l:
        return "Norovirus"
    if "plague" in l:
        return "Plague"
    if "leprosy" in l:
        return "Leprosy"
    if "anthrax" in l:
        return "Anthrax"
    # Add more if needed
    return None


def audit_mapping(apply: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not MAP_PATH.exists():
        raise FileNotFoundError(f"Missing mapping file: {MAP_PATH}")
    if not WHO_WEEKLY_PATH.exists():
        raise FileNotFoundError(f"Missing WHO weekly file: {WHO_WEEKLY_PATH}")

    weekly = pd.read_csv(WHO_WEEKLY_PATH)
    mapping = pd.read_csv(MAP_PATH)

    # Normalize columns
    for c in ["disease_label", "indicator_code"]:
        if c not in weekly.columns:
            raise ValueError(f"WHO weekly missing column: {c}")
    for c in ["disease_label", "indicator_code", "canonical_disease"]:
        if c not in mapping.columns:
            raise ValueError(f"Mapping missing column: {c}")

    # Unique label-indicator pairs from weekly data
    uniq = (
        weekly[["disease_label", "indicator_code"]]
        .drop_duplicates()
        .assign(count=0)
    )
    # Count rows per pair for prioritization
    counts = (
        weekly.groupby(["disease_label", "indicator_code"], as_index=False)["cases"]
        .count()
        .rename(columns={"cases": "rows"})
    )
    uniq = uniq.merge(counts, on=["disease_label", "indicator_code"], how="left")

    # Join to existing mapping
    joined = uniq.merge(mapping, on=["disease_label", "indicator_code"], how="left")
    joined["canonical_disease"] = joined["canonical_disease"].fillna("")

    # Suggest canonical for blanks
    joined["suggested"] = joined["disease_label"].apply(suggest_canonical)
    missing = joined[joined["canonical_disease"] == ""].copy()
    print(f"[AUDIT] Unique WHO pairs: {len(joined)}; mapped: {len(joined) - len(missing)}; unmapped: {len(missing)}")

    # Preview top unmapped suggestions
    preview = missing.copy()
    preview["suggested"] = preview["suggested"].fillna("<none>")
    preview = preview.sort_values("rows", ascending=False)
    print("[TOP UNMAPPED SUGGESTIONS]")
    for _, r in preview.head(20).iterrows():
        print(f"- label='{r['disease_label']}', indicator='{r['indicator_code']}', rows={r['rows']}, suggested='{r['suggested']}'")

    if apply:
        # Apply suggestions where available; leave others blank for manual curation
        to_update = missing[missing["suggested"].notna()].copy()
        if not to_update.empty:
            updated = mapping.merge(to_update[["disease_label", "indicator_code", "suggested"]],
                                    on=["disease_label", "indicator_code"], how="left")
            updated["canonical_disease"] = updated["canonical_disease"].fillna("")
            need_fill = (updated["canonical_disease"] == "") & updated["suggested"].notna()
            updated.loc[need_fill, "canonical_disease"] = updated.loc[need_fill, "suggested"]

            # Backup and write
            backup = MAP_PATH.with_name(f"who_indicator_mapping_backup_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            mapping.to_csv(backup, index=False)
            updated.drop(columns=["suggested"], inplace=True)
            updated.to_csv(MAP_PATH, index=False)
            print(f"[APPLY] Wrote updated mapping: {MAP_PATH} (backup: {backup})")
        else:
            print("[APPLY] No suggestions to apply; mapping already complete or needs manual curation.")

    return joined, missing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply suggestions to fill canonical_disease where possible")
    args = parser.parse_args()
    audit_mapping(apply=args.apply)


if __name__ == "__main__":
    main()