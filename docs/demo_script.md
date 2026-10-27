# GoldLens demo script (2–3 minutes)

## 0:00–0:20 — Problem

“MCX sells the same underlying gold through four futures contracts with different lot sizes, quote bases, purities, and expiry windows. A raw price comparison can make one contract look cheap when that difference is mechanical. GoldLens asks whether any apparent difference survives the adjustments and realistic trading costs.”

Show the dashboard title and the four-contract comparison controls.

## 0:20–0:50 — Data and normalization

“We use the supplied public MCX Bhavcopy reports. The ingestion step validates dates from report contents, not filenames, and stores each symbol, expiry, and date separately in DuckDB. GoldLens converts every quote to rupees per gram at 999 purity before it compares contracts.”

Show the data-quality panel, then the normalized spread panel. Point out two actual expiry dates in the selector/trace labels.

## 0:50–1:25 — Rigorous signal construction

“The chart is an exact-expiry-pair spread in basis points. Its normal band uses only prior observations, so it has no future-data leakage. We retain the expiry gap and use the curve to separate purity, carry/roll-down, and any residual. A potential watch also needs reported volume and open interest.”

Show a selected spread trace, its prior-only band, and the calendar/carry information. State that the series is not stitched.

## 1:25–1:55 — Conservative backtest and costs

“A signal today enters on the next observed trading day, with whole lots and matched notionals. The replay separates the train and test periods. We charge the costs of the contracts actually held: brokerage, exchange and regulatory charges, tax, slippage, margin financing, and a thin-day haircut.”

Show the backtest/cost scenario panel and call out the low, base, and high scenarios.

## 1:55–2:25 — Result and honest verdict

“For the supplied data, the gross replay is slightly positive, but the net result is negative in every modeled cost scenario. The current verdict is not a trading recommendation—it is that no persistent edge survives the modeled costs. The app also states the key limitations: Close is a settlement proxy, and several contract and cost inputs remain marked for verification.”

Show the verdict and limitations/data-quality panels.

## 2:25–2:45 — Close

“GoldLens turns an attractive-looking raw quote difference into an auditable research question. It helps rule out mechanical artifacts before anyone treats a spread as an opportunity.”

End on the architecture diagram or dashboard overview.
