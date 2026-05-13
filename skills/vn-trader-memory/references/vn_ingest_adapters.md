# VN Ingest Adapters — Per-screener contracts

`scripts/vn_thesis_ingest.py` ships adapters for four VN-prefixed screeners.
Each adapter reads one record from the screener's JSON output and produces a
`thesis_data` dict for `vn_thesis_store.register()`.

## Top-level fields the ingester reads

| Key in JSON output | What ingester does with it |
| --- | --- |
| `as_of` / `generated_at` / `report_date` | Sets `_source_date` so `created_at` and the thesis_id date match the report, not wall-clock. |
| `results` / `candidates` / `rows` / `screened` | Treated as the list of records to ingest. |
| Top-level `ticker` or `symbol` | Treated as a single-record output. |

## Per-record fields read by every adapter

| Record field | Purpose |
| --- | --- |
| `ticker` *or* `symbol` | **Required.** Becomes `thesis.ticker`. |
| `exchange` | Normalised to `hose` / `hnx` / `upcom` / `null`. `hsx` is accepted as an alias for HOSE. |
| `grade` | Stored as `origin.screening_grade`. |
| `score` | Stored as `origin.screening_score`. |
| (all other keys) | Stored verbatim under `origin.raw_provenance` for postmortem replay. |

## vn-vcp-screener

| Record field | Mapped to |
| --- | --- |
| `pivot_price` | `entry.target_price` |
| `stop_loss` | `exit.stop_loss` |
| `contractions` | Mentioned in `thesis_statement` |

Thesis type: `pivot_breakout`. Setup type: `vcp_breakout`.

## vn-pullback-screener

| Record field | Mapped to |
| --- | --- |
| `entry_price` | `entry.target_price` |
| `stop_loss` | `exit.stop_loss` |
| `rsi` | Mentioned in `thesis_statement` |
| `distance_from_ma20_pct` | Mentioned in `thesis_statement` |

Thesis type: `mean_reversion`. Setup type: `ma20_pullback`.

## vn-dividend-screener

| Record field | Mapped to |
| --- | --- |
| `entry_price` | `entry.target_price` |
| `stop_loss` | `exit.stop_loss` |
| `dividend_yield_pct` | Mentioned in `thesis_statement` |
| `payout_ratio` | Mentioned in `thesis_statement` |

Thesis type: `dividend_income`. Setup type: `dividend_yield_pullback`.

## vn-breakout-trade-planner

| Record field | Mapped to |
| --- | --- |
| `entry_price` | `entry.target_price` |
| `stop_loss` | `exit.stop_loss` |
| `take_profit` | `exit.take_profit` |
| `r_multiple` | `exit.take_profit_rr` |

Thesis type: `pivot_breakout`. Setup type: `breakout_plan`.

## Idempotency

`register()` computes an `origin_fingerprint` from
`(ticker, thesis_type, thesis_statement, _source_date, origin.skill, raw_provenance)`.
Running the same screener output through ingest twice returns the existing
thesis_id rather than creating a duplicate.

## Adding a new adapter

```python
from vn_thesis_ingest import _adapter

@_adapter("my-new-vn-screener")
def ingest_my_new(record: dict, input_file: str) -> dict:
    ticker = record.get("ticker") or record.get("symbol")
    if not ticker:
        raise ValueError("Missing ticker")
    return {
        "ticker": ticker,
        "thesis_type": "pivot_breakout",
        "thesis_statement": f"{ticker} ...",
        "_register_reason": "screened by my-new-vn-screener",
        "origin": {
            "skill": "my-new-vn-screener",
            "output_file": input_file,
            "screening_grade": record.get("grade"),
            "screening_score": record.get("score"),
            "raw_provenance": dict(record),
        },
    }
```
