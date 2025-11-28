"""Analyze predictions vs thresholds for Ebola and Malaria"""
import pandas as pd
import numpy as np
from pathlib import Path

# Load evaluation predictions
REPORTS_DIR = Path("reports/production")
diseases = ["ebola", "malaria"]

print("=== Prediction vs Threshold Analysis ===\n")

for disease in diseases:
    pred_file = REPORTS_DIR / f"eval_predictions_{disease}.csv"
    if not pred_file.exists():
        print(f"Skipping {disease}: file not found")
        continue
        
    df = pd.read_csv(pred_file)
    
    # Calculate actual stats
    actual_max = df['actual'].max()
    actual_75 = np.percentile(df['actual'], 75)
    actual_mean = df['actual'].mean()
    
    # Calculate predicted stats
    pred_max = df['predicted'].max()
    pred_75 = np.percentile(df['predicted'], 75)
    pred_mean = df['predicted'].mean()
    
    print(f"Disease: {disease.upper()}")
    print(f"  Actual Stats:   Max={actual_max:.2f}, 75th%={actual_75:.2f}, Mean={actual_mean:.2f}")
    print(f"  Predicted Stats: Max={pred_max:.2f}, 75th%={pred_75:.2f}, Mean={pred_mean:.2f}")
    
    # Check how many predictions exceed the ACTUAL 75th percentile (which is roughly the threshold used)
    # Note: The real threshold is per-state, but this gives a global idea
    exceeds_threshold = (df['predicted'] >= actual_75).sum()
    total = len(df)
    pct = (exceeds_threshold / total) * 100
    
    print(f"  Predictions >= Actual 75th%: {exceeds_threshold}/{total} ({pct:.1f}%)")
    
    if exceeds_threshold == 0:
        print("  ❌ PROBLEM CONFIRMED: No predictions reach the threshold.")
        print("     The model under-predicts magnitude, so predictions never trigger the alert.")
    else:
        print(f"  ⚠️ Some predictions reach global threshold, but maybe not local state thresholds.")
    print()
