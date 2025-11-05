import pandas as pd
import pathlib
from live_data.standardize import append_and_dedupe, log_ingest


def test_append_and_dedupe_preserves_unique_rows():
    tmp = pathlib.Path("data/live/_tmp_append.csv")
    try:
        if tmp.exists():
            tmp.unlink()
        # First append
        df1 = pd.DataFrame({"key": [1, 2], "val": ["a", "b"]})
        append_and_dedupe(tmp, df1, key_cols=["key"])  # create file
        # Second append with one duplicate and one new
        df2 = pd.DataFrame({"key": [2, 3], "val": ["b2", "c"]})
        append_and_dedupe(tmp, df2, key_cols=["key"])  # dedupe
        out = pd.read_csv(tmp)
        # Expect keys 1,2,3 with latest for key=2
        assert sorted(out["key"].tolist()) == [1, 2, 3]
        # Verify overwrite behavior selects latest row for duplicate key
        row2 = out[out["key"] == 2].iloc[0]
        assert row2["val"] == "b2"
    finally:
        if tmp.exists():
            tmp.unlink()


def test_log_ingest_writes_entry_to_default_log():
    # Create a dummy target file path and log ingestion
    target_path = pathlib.Path("data/live/_tmp_target.csv")
    try:
        target_path.write_text("col\nval\n")
        log_ingest(source="unit_test_source", new_rows=5, written_rows=5, path=target_path)
        # Read default ingest log
        log_path = pathlib.Path("data/live/ingest_log.csv")
        assert log_path.exists()
        df = pd.read_csv(log_path)
        assert (df["source"] == "unit_test_source").any()
    finally:
        if target_path.exists():
            target_path.unlink()