import os
import json
import pandas as pd

PREDICTIONS_CSV = os.path.join('reports', 'production', 'predictions_live.csv')
SUMMARY_JSON = os.path.join('reports', 'production', 'predictions_summary.json')
TOP10_CASES_CSV = os.path.join('reports', 'production', 'predictions_top10_cases.csv')
TOP10_DEATHS_CSV = os.path.join('reports', 'production', 'predictions_top10_deaths.csv')


def load_predictions(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Predictions file not found: {path}")
    df = pd.read_csv(path)
    # Normalize columns and coerce numeric types
    for col in ['pred_year', 'pred_week', 'pred_cases_next_week', 'pred_deaths_next_week']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # Drop filler rows without state or disease
    df = df.dropna(subset=['state', 'disease'], how='any')
    return df


def summarize(df: pd.DataFrame) -> dict:
    diseases = sorted(df['disease'].dropna().unique().tolist())
    summary = {
        'row_count': int(len(df)),
        'unique_diseases_count': int(len(diseases)),
        'unique_diseases': diseases,
        'totals_by_disease': {},
        'global_top10_cases': [],
        'global_top10_deaths': [],
        'top_states_by_disease': {}
    }

    # Totals per disease
    totals = (
        df.groupby('disease')[['pred_cases_next_week', 'pred_deaths_next_week']]
        .sum()
        .sort_values(by='pred_cases_next_week', ascending=False)
    )
    for disease, row in totals.iterrows():
        summary['totals_by_disease'][disease] = {
            'cases_sum': float(row['pred_cases_next_week']),
            'deaths_sum': float(row['pred_deaths_next_week'])
        }

    # Global top10 cases
    top_cases = df.sort_values(by='pred_cases_next_week', ascending=False).head(10)
    summary['global_top10_cases'] = [
        {
            'rank': int(i + 1),
            'state': str(r['state']),
            'disease': str(r['disease']),
            'cases': float(r['pred_cases_next_week']),
            'deaths': float(r['pred_deaths_next_week'] or 0)
        }
        for i, r in top_cases.iterrows()
    ]

    # Global top10 deaths
    top_deaths = df.sort_values(by='pred_deaths_next_week', ascending=False).head(10)
    summary['global_top10_deaths'] = [
        {
            'rank': int(i + 1),
            'state': str(r['state']),
            'disease': str(r['disease']),
            'cases': float(r['pred_cases_next_week']),
            'deaths': float(r['pred_deaths_next_week'])
        }
        for i, r in top_deaths.iterrows()
    ]

    # Top states by disease (aggregate across rows)
    for disease in diseases:
        ddf = df[df['disease'] == disease]
        agg = (
            ddf.groupby('state')[['pred_cases_next_week', 'pred_deaths_next_week']]
            .sum()
            .sort_values(by='pred_cases_next_week', ascending=False)
            .head(5)
        )
        summary['top_states_by_disease'][disease] = [
            {
                'state': str(idx),
                'cases_sum': float(row['pred_cases_next_week']),
                'deaths_sum': float(row['pred_deaths_next_week'])
            }
            for idx, row in agg.iterrows()
        ]

    return summary


def save_reports(summary: dict, df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(SUMMARY_JSON), exist_ok=True)
    with open(SUMMARY_JSON, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    # Save CSVs for top10s
    cases_df = pd.DataFrame(summary['global_top10_cases'])
    deaths_df = pd.DataFrame(summary['global_top10_deaths'])
    cases_df.to_csv(TOP10_CASES_CSV, index=False)
    deaths_df.to_csv(TOP10_DEATHS_CSV, index=False)


def main():
    df = load_predictions(PREDICTIONS_CSV)
    summary = summarize(df)
    save_reports(summary, df)

    # Print concise console summary
    print("=== Predictions Summary ===")
    print(f"Rows: {summary['row_count']}")
    print(f"Diseases: {summary['unique_diseases_count']} -> {', '.join(summary['unique_diseases'])}")

    # Top 3 diseases by cases
    totals = [
        (d, v['cases_sum'], v['deaths_sum'])
        for d, v in summary['totals_by_disease'].items()
    ]
    totals.sort(key=lambda x: x[1], reverse=True)
    print("\nTop 3 Diseases by Predicted Cases:")
    for i, (d, c, dd) in enumerate(totals[:3], 1):
        print(f" {i}. {d}: cases={c:.2f}, deaths={dd:.2f}")

    # Global top 5 cases
    print("\nGlobal Top 5 by Predicted Cases:")
    for row in summary['global_top10_cases'][:5]:
        print(f" {row['rank']}. {row['state']} - {row['disease']}: cases={row['cases']:.2f}, deaths={row['deaths']:.2f}")

    # Hints for where files are saved
    print("\nReports written:")
    print(f" - {SUMMARY_JSON}")
    print(f" - {TOP10_CASES_CSV}")
    print(f" - {TOP10_DEATHS_CSV}")


if __name__ == '__main__':
    main()