"""Check actual confusion matrix values from console_report evaluation"""
import pandas as pd

df = pd.read_csv('reports/production/evaluation_metrics.csv')

print("Checking confusion matrix values for each disease:\n")
for _, row in df.iterrows():
    disease = row['disease']
    pos = row['positive']
    neg = row['negative']
    prec_w = row['precision_weighted_pct']
    prec_pos = row['precision_pos_pct']
    prec_neg = row['precision_neg_pct']
    
    print(f"{disease}:")
    print(f"  Positive samples: {pos}")
    print(f"  Negative samples: {neg}")
    print(f"  Precision (weighted): {prec_w}")
    print(f"  Precision (positive class): {prec_pos}")
    print(f"  Precision (negative class): {prec_neg}")
    
    if pd.isna(prec_w):
        print(f"  ❌ ISSUE: Weighted precision is NaN")
        if pd.isna(prec_pos):
            print(f"     - Positive class precision is NaN (likely tp=0 AND fp=0)")
        if pd.isna(prec_neg):
            print(f"     - Negative class precision is NaN (likely tn=0 AND fn=0)")
    print()
