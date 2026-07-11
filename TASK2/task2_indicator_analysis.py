#!/usr/bin/env python3
"""TASK2: 从 TASK1 行情计算技术指标，并生成 CSV 与网页数据。"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
RESULT_DIR = ROOT / "TASK2" / "results"
COMPANIES = {
    "600276_SH": "恒瑞医药",
    "688235_SH": "百济神州",
    "688180_SH": "君实生物",
    "600196_SH": "复星医药",
}
NUMERIC_COLUMNS = ["open", "high", "low", "close", "vol", "amount", "pct_chg"]


def load_price(code: str) -> pd.DataFrame:
    data = pd.read_csv(ASSET_DIR / f"{code}_daily.csv", encoding="utf-8-sig")
    data["trade_date"] = pd.to_datetime(data["trade_date"].astype(str), format="%Y%m%d")
    return data.sort_values("trade_date").reset_index(drop=True)


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    delta = data["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    data["rsi14"] = 100 - 100 / (1 + rs)

    data["ema12"] = data["close"].ewm(span=12, adjust=False).mean()
    data["ema26"] = data["close"].ewm(span=26, adjust=False).mean()
    data["macd"] = data["ema12"] - data["ema26"]
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["macd_hist"] = data["macd"] - data["macd_signal"]

    data["bb_mid"] = data["close"].rolling(20).mean()
    std20 = data["close"].rolling(20).std(ddof=0)
    data["bb_upper"] = data["bb_mid"] + 2 * std20
    data["bb_lower"] = data["bb_mid"] - 2 * std20
    data["bb_width"] = data["bb_upper"] - data["bb_lower"]

    low9 = data["low"].rolling(9).min()
    high9 = data["high"].rolling(9).max()
    data["kdj_rsv"] = (data["close"] - low9) / (high9 - low9) * 100
    data["kdj_k"] = data["kdj_rsv"].ewm(alpha=1 / 3, adjust=False).mean()
    data["kdj_d"] = data["kdj_k"].ewm(alpha=1 / 3, adjust=False).mean()
    data["kdj_j"] = 3 * data["kdj_k"] - 2 * data["kdj_d"]
    return data


def rounded(value, digits=2):
    return None if pd.isna(value) else round(float(value), digits)


def build_company(code: str, name: str) -> tuple[dict, list[dict]]:
    data = add_indicators(load_price(code))
    output = data.copy()
    output["trade_date"] = output["trade_date"].dt.strftime("%Y-%m-%d")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(RESULT_DIR / f"{code}_indicators.csv", index=False, encoding="utf-8-sig")

    description = data[NUMERIC_COLUMNS].describe().round(4).to_dict()
    description = {
        column: {key: rounded(value, 4) for key, value in values.items()}
        for column, values in description.items()
    }
    latest = data.iloc[-1]
    summary = {
        "stock": name,
        "code": code.replace("_", "."),
        "rows": len(data),
        "start_date": data["trade_date"].iloc[0].strftime("%Y-%m-%d"),
        "end_date": data["trade_date"].iloc[-1].strftime("%Y-%m-%d"),
        "missing": {key: int(value) for key, value in data.iloc[:, :9].isna().sum().items()},
        "description": description,
        "indicator_csv": f"TASK2/results/{code}_indicators.csv",
        "return_pct": rounded((data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100),
        "latest": {
            "date": latest["trade_date"].strftime("%Y-%m-%d"),
            **{key: rounded(latest[key], 4 if key.startswith("macd") else 2) for key in
               ["close", "rsi14", "macd", "macd_signal", "macd_hist", "bb_upper", "bb_mid", "bb_lower", "kdj_k", "kdj_d", "kdj_j"]},
        },
    }
    record_columns = ["trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg",
                      "rsi14", "macd", "macd_signal", "macd_hist", "bb_upper", "bb_mid", "bb_lower",
                      "kdj_k", "kdj_d", "kdj_j"]
    records = []
    for _, row in output[record_columns].iterrows():
        records.append({key: (None if pd.isna(value) else value) for key, value in row.items()})
    return summary, records


def main() -> None:
    companies = []
    records_by_company = []
    for code, name in COMPANIES.items():
        summary, records = build_company(code, name)
        companies.append(summary)
        records_by_company.append(records)

    payload = {
        "summary": companies[0],
        "companies": [
            {"summary": summary, "records": records}
            for summary, records in zip(companies, records_by_company)
        ],
    }
    (ASSET_DIR / "task2_data.js").write_text(
        "window.TASK2_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"已生成 {len(companies)} 家公司的 TASK2 指标数据。")


if __name__ == "__main__":
    main()
