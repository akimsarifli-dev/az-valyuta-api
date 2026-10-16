import json
import requests
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

rates_list = []

# 1. ABB (Azərbaycan Beynəlxalq Bankı) - Rəsmi API
try:
    resp = requests.get("https://abb-bank.az/api/currencies/rates", headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get("data", []):
            curr = item.get("code")
            if curr in ["USD", "EUR", "RUB"]:
                rates_list.append({
                    "bank": "ABB",
                    "currency": curr,
                    "cash_buy": str(item.get("cashBuyRate", "-")),
                    "cash_sell": str(item.get("cashSellRate", "-")),
                    "cashless_buy": str(item.get("cardBuyRate", "-")),
                    "cashless_sell": str(item.get("cardSellRate", "-"))
                })
except Exception as e:
    print(f"ABB xətası: {e}")

# 2. Kapital Bank (Birbank) - Rəsmi API
try:
    resp = requests.get("https://kapitalbank.az/api/currencies", headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get("currencies", []):
            curr = item.get("code")
            if curr in ["USD", "EUR", "RUB"]:
                rates_list.append({
                    "bank": "Kapital Bank",
                    "currency": curr,
                    "cash_buy": str(item.get("cashBuy", "-")),
                    "cash_sell": str(item.get("cashSell", "-")),
                    "cashless_buy": str(item.get("cardBuy", "-")),
                    "cashless_sell": str(item.get("cardSell", "-"))
                })
except Exception as e:
    print(f"Kapital Bank xətası: {e}")

# 3. Yelo Bank - Rəsmi API
try:
    resp = requests.get("https://www.yelo.az/api/rates/", headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        for item in data:
            curr = item.get("currency")
            if curr in ["USD", "EUR", "RUB"]:
                rates_list.append({
                    "bank": "Yelo Bank",
                    "currency": curr,
                    "cash_buy": str(item.get("cash_buy", "-")),
                    "cash_sell": str(item.get("cash_sell", "-")),
                    "cashless_buy": str(item.get("non_cash_buy", "-")),
                    "cashless_sell": str(item.get("non_cash_sell", "-"))
                })
except Exception as e:
    print(f"Yelo Bank xətası: {e}")

# Nəticəni yadda saxlayırıq
result = {
    "success": True,
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
    "total_records": len(rates_list),
    "rates": rates_list
}

with open("rates.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Tamamlandı. Çəkilən real sətir sayı: {len(rates_list)}")
