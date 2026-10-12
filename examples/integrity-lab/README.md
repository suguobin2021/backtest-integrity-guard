# Backtest Integrity Lab: profitable-looking, non-causal fills

**Run in under a minute** from the repository root after installing the package:

```bash
git clone https://github.com/suguobin2021/backtest-integrity-guard.git
cd backtest-integrity-guard
python3 -m pip install -e .
python3 examples/integrity-lab/demo.py
```

The script generates **12 entirely synthetic trades**, with deliberately favorable close-to-next-open gaps. Both cases use the *same* synthetic signal directions, next-bar exits, and fixed 0.10 price-unit cost per trade.

- **Naive:** uses the signal bar's closing price as the entry fill at that bar's close, after consuming the close. This is not a causal executable fill under the declared signal timing.
- **Causal:** enters at the next bar's open (modeled one second after the signal close). This is a simplified next-bar timing illustration, not a real exchange fill simulator.

Expected deterministic output:

```text
naive: audit=FAIL findings=12 net_price_units=+15.00
causal: audit=PASS findings=0 net_price_units=+3.00
Illustration only: synthetic prices intentionally create a 12.00-unit gap.
The auditor checks timestamps; it does not verify prices, P&L, or slippage.
```

**Important limitations:** these are *price-unit sums*, not percent returns, profit factor, or portfolio performance. The synthetic gap pattern was designed to illustrate bias, not sampled from any market. The guard audits **declared timestamps and consistency rules**; it cannot establish that reported fills, prices, execution costs, or realized profits are authentic. Passing an audit is not proof of a profitable or fully causal trading system. This demo does not change the project's existing execution semantics or the open bar-completion issue.

## Reproduce the audit independently

The demo creates two temporary CSV ledgers and invokes the public `btguard ledger` audit for each. It asserts both audit outcomes and the illustrative arithmetic, then deletes the temporary files. To inspect the underlying timestamp rule, run `btguard ledger examples/lookahead_entry.csv` (expected FAIL).

GitHub Actions runs the demo on Python 3.10, 3.11, and 3.12 alongside the existing unit tests. The lab is not a benchmark of prediction quality, live execution, or returns.
