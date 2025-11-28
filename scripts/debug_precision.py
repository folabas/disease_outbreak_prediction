"""Debug script to check why precision is NaN for ebola and malaria"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from ml.features import FEATURES
from ml.train_deep import WINDOW_SIZE, load_and_prepare_data

# Load data
df = load_and_prepare_data()
df = df.dropna(subset=["state", "disease", "year", "week", "cases"]).reset_index(drop=True)

for col in FEATURES:
    if col not in df.columns:
        df[col] = 0.0
df[FEATURES] = df[FEATURES].ffill().bfill()
df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

# Create sequences for ebola only
df_ebola = df[df['disease'] == 'ebola'].copy()
df_ebola = df_ebola.sort_values(['state', 'year', 'week']).reset_index(drop=True)

print(f"\n=== Ebola Data Analysis ===")
print(f"Total ebola rows: {len(df_ebola)}")
print(f"Unique states: {df_ebola['state'].nunique()}")
print(f"Cases stats: min={df_ebola['cases'].min()}, max={df_ebola['cases'].max()}, mean={df_ebola['cases'].mean():.2f}")

# Check threshold (75th percentile)
threshold_75 = np.percentile(df_ebola['cases'], 75)
print(f"75th percentile threshold: {threshold_75:.2f}")

# Check how many are above/below threshold
above = (df_ebola['cases'] >= threshold_75).sum()
below = (df_ebola['cases'] < threshold_75).sum()
print(f"Cases >= threshold: {above}")
print(f"Cases < threshold: {below}")

# Simulate classification
# Split into train/test (80/20)
split = int(len(df_ebola) * 0.8)
train_cases = df_ebola['cases'].iloc[:split]
test_cases = df_ebola['cases'].iloc[split:]

train_threshold = np.percentile(train_cases, 75)
print(f"\nTrain threshold (75th percentile): {train_threshold:.2f}")

# Classify test set
y_true_cls = (test_cases >= train_threshold).astype(int)
# Simulate predictions (for now, just use actual values)
y_pred_cls = y_true_cls.copy()  # Perfect prediction to see if metrics work

print(f"\nTest set classification:")
print(f"Positive class (outbreak): {(y_true_cls == 1).sum()}")
print(f"Negative class (normal): {(y_true_cls == 0).sum()}")

# Calculate confusion matrix
tp = int(np.sum((y_true_cls == 1) & (y_pred_cls == 1)))
tn = int(np.sum((y_true_cls == 0) & (y_pred_cls == 0)))
fp = int(np.sum((y_true_cls == 0) & (y_pred_cls == 1)))
fn = int(np.sum((y_true_cls == 1) & (y_pred_cls == 0)))

print(f"\nConfusion Matrix:")
print(f"TP (true positive): {tp}")
print(f"TN (true negative): {tn}")
print(f"FP (false positive): {fp}")
print(f"FN (false negative): {fn}")

# Calculate precision
if (tp + fp) > 0:
    prec_pos = tp / (tp + fp) * 100
    print(f"\nPrecision (positive class): {prec_pos:.2f}%")
else:
    print(f"\nPrecision (positive class): UNDEFINED (tp + fp = 0)")

if (tn + fn) > 0:
    prec_neg = tn / (tn + fn) * 100
    print(f"Precision (negative class): {prec_neg:.2f}%")
else:
    print(f"Precision (negative class): UNDEFINED (tn + fn = 0)")

print("\n" + "="*60)
print("DIAGNOSIS:")
if (tp + fp) == 0:
    print("❌ No positive predictions made (tp + fp = 0)")
    print("   This means the model NEVER predicts outbreak for ebola")
if (tn + fn) == 0:
    print("❌ No negative predictions made (tn + fn = 0)")
    print("   This means the model ALWAYS predicts outbreak for ebola")
