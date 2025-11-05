from pathlib import Path

from live_data.pipeline import run_realtime_mode, run_cached_mode


def test_run_realtime_mode(tmp_path: Path):
    out = run_realtime_mode()
    assert out.exists()


def test_run_cached_mode_if_available():
    best = Path.cwd() / "reports" / "production" / "predictions_best_by_disease.csv"
    if best.exists():
        out = run_cached_mode(best)
        assert out.exists()