"""Synthetic, deterministic illustration of same-bar execution bias.

No market data, trading strategy, or profitability inference is involved.
Run from the repository root: python3 examples/integrity-lab/demo.py
"""
import csv
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
ROWS = []
for i in range(12):
    # Synthetic, deliberately biased close-to-next-open gaps.
    signal_close = 100.0
    next_open = 101.0 if i % 2 == 0 else 99.0
    direction = 1 if i % 2 == 0 else -1
    next_exit = next_open + direction * 0.35
    timestamp = START + timedelta(minutes=10 * i + 5)
    ROWS.append((timestamp, direction, signal_close, next_open, next_exit))

def iso(t):
    return t.isoformat().replace("+00:00", "Z")

def run():
    naive = []
    causal = []
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)
        for mode in ("naive", "causal"):
            ledger = path / (mode + ".csv")
            with ledger.open("w", newline="") as out:
                writer = csv.writer(out)
                writer.writerow(("signal_bar_close", "next_bar_open", "entry_time",
                                 "stop_hit", "target_hit", "same_bar_policy"))
                for t, direction, close, next_open, exit_price in ROWS:
                    entry = close if mode == "naive" else next_open
                    entry_time = t if mode == "naive" else t + timedelta(seconds=1)
                    writer.writerow((iso(t), iso(t), iso(entry_time), "false", "false", ""))
                    # Fixed synthetic price-unit cost, applied on both legs in aggregate.
                    pnl = direction * (exit_price - entry) - 0.10
                    (naive if mode == "naive" else causal).append(round(pnl, 8))
            cmd = [sys.executable, "-m", "backtest_integrity_guard.cli", "ledger", str(ledger)]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            if not result.stdout:
                raise RuntimeError(result.stderr or "No audit JSON")
            report = json.loads(result.stdout)
            expected = "FAIL" if mode == "naive" else "PASS"
            assert report["status"] == expected, report
            if mode == "naive":
                assert "LOOKAHEAD_OR_SAME_BAR_ENTRY" in [f["code"] for f in report["findings"]]
            print(f"{mode}: audit={report['status']} findings={report['errors']} "
                  f"net_price_units={sum(naive if mode == 'naive' else causal):+.2f}")
    assert round(sum(naive), 2) == 15.0
    assert round(sum(causal), 2) == 3.0
    print("Illustration only: synthetic prices intentionally create a 12.00-unit gap.")
    print("The auditor checks timestamps; it does not verify prices, P&L, or slippage.")

if __name__ == "__main__":
    run()
