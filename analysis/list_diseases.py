import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from ml.data import load_dataset, get_diseases
from ml.config import DATA_PATH


def main():
    df = load_dataset(DATA_PATH)
    diseases = get_diseases(df)
    print("diseases:", diseases)
    counts = df["disease"].value_counts().to_dict()
    print("counts:", counts)


if __name__ == "__main__":
    main()