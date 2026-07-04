from __future__ import annotations

import csv
import json
import os
import statistics
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path


TOKEN = os.getenv("TUSHARE_TOKEN")
OUT_DIR = Path(__file__).resolve().parent / "assets"
COMPANIES = [
    {"code": "600276.SH", "name": "恒瑞医药", "role": "本土创新药转型龙头", "focus": "肿瘤、麻醉、代谢、自免", "theme": "从仿制药优势向创新药平台升级，PD-1、ADC、小分子与国际化并行。"},
    {"code": "688235.SH", "name": "百济神州", "role": "全球化创新药代表", "focus": "肿瘤、自研商业化、海外临床", "theme": "中国创新药全球临床和商业化能力的代表，拥有BTK抑制剂、PD-1等核心资产。"},
    {"code": "688180.SH", "name": "君实生物", "role": "免疫肿瘤先行者", "focus": "PD-1、感染、自免、出海授权", "theme": "以特瑞普利单抗为核心，探索免疫肿瘤、感染与国际注册路径。"},
    {"code": "600196.SH", "name": "复星医药", "role": "综合医药平台型龙头", "focus": "创新药、疫苗、器械、国际化", "theme": "以多元化医药平台承接创新药、疫苗和全球化业务，具备较强产业整合能力。"},
]


def tushare_call(api_name: str, params: dict, fields: str) -> tuple[list[str], list[list]]:
    if not TOKEN:
        raise RuntimeError("请先设置环境变量 TUSHARE_TOKEN。")
    payload = {"api_name": api_name, "token": TOKEN, "params": params, "fields": fields}
    request = urllib.request.Request(
        "http://api.tushare.pro",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("code") != 0:
        raise RuntimeError(f"Tushare 接口调用失败：{result.get('msg')}")
    return result["data"]["fields"], result["data"]["items"]


def build_dataset() -> dict:
    end = datetime.today()
    start = end - timedelta(days=365)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    companies = []

    for company in COMPANIES:
        fields, items = tushare_call(
            "daily",
            {
                "ts_code": company["code"],
                "start_date": start.strftime("%Y%m%d"),
                "end_date": end.strftime("%Y%m%d"),
            },
            "ts_code,trade_date,open,high,low,close,vol,amount,pct_chg",
        )
        rows = [dict(zip(fields, item)) for item in items]
        rows.sort(key=lambda row: row["trade_date"])
        closes = [float(row["close"]) for row in rows]
        pct = [float(row["pct_chg"]) for row in rows if row["pct_chg"] is not None]

        peak = closes[0]
        max_drawdown = 0.0
        for value in closes:
            peak = max(peak, value)
            max_drawdown = min(max_drawdown, (value / peak - 1) * 100)

        csv_name = f"{company['code'].replace('.', '_')}_daily.csv"
        with (OUT_DIR / csv_name).open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

        companies.append({
            **company,
            "records": len(rows),
            "startDate": rows[0]["trade_date"],
            "endDate": rows[-1]["trade_date"],
            "startClose": round(closes[0], 2),
            "endClose": round(closes[-1], 2),
            "returnPct": round((closes[-1] / closes[0] - 1) * 100, 2),
            "highClose": round(max(closes), 2),
            "lowClose": round(min(closes), 2),
            "avgTurnoverYi": round(sum(float(row["amount"]) for row in rows) / len(rows) / 100000, 2),
            "dailyVolPct": round(statistics.pstdev(pct), 2) if len(pct) > 1 else 0,
            "maxDrawdownPct": round(max_drawdown, 2),
            "csv": f"assets/{csv_name}",
            "series": [
                {
                    "date": row["trade_date"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["vol"]),
                    "amount": float(row["amount"]),
                    "pct": float(row["pct_chg"]),
                }
                for row in rows
            ],
        })

    return {
        "generatedAt": generated,
        "source": "Tushare Pro daily API",
        "range": {"start": start.strftime("%Y%m%d"), "end": end.strftime("%Y%m%d")},
        "companies": companies,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset()
    (OUT_DIR / "data.json").write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "data.js").write_text(
        "window.PHARMA_DATA = " + json.dumps(dataset, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"已生成 {len(dataset['companies'])} 家公司的数据。")


if __name__ == "__main__":
    main()
