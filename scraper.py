import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_real_bank_rates():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    rates_list = []
    
    # 1. Banco.az saytından real bank kurlarını çəkirik
    try:
        url = "https://banco.az/az/currency/rates"
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            # Əgər birbaşa JSON verirsə
            for item in data.get("rates", []):
                rates_list.append({
                    "bank": item.get("bank_name", "Naməlum"),
                    "currency": item.get("currency", "USD"),
                    "cash_buy": str(item.get("cash_buy", "-")),
                    "cash_sell": str(item.get("cash_sell", "-")),
                    "cashless_buy": str(item.get("card_buy", item.get("cash_buy", "-"))),
                    "cashless_sell": str(item.get("card_sell", item.get("cash_sell", "-")))
                })
    except Exception as e:
        print(f"Banco API xətası: {e}")

    # 2. Əgər JSON gəlməzsə, HTML cədvəlindən canlı oxuyuruq
    if not rates_list:
        try:
            table_url = "https://banker.az/valyuta-mezenneleri/"
            resp = requests.get(table_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                rows = soup.find_all("tr")
                for row in rows:
                    cols = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cols) >= 5 and ("USD" in cols or "EUR" in cols or "RUB" in cols):
                        rates_list.append({
                            "bank": cols[0],
                            "currency": cols[1],
                            "cash_buy": cols[2],
                            "cash_sell": cols[3],
                            "cashless_buy": cols[4] if len(cols) > 4 else cols[2],
                            "cashless_sell": cols[5] if len(cols) > 5 else cols[3]
                        })
        except Exception as e:
            print(f"Banker cədvəl xətası: {e}")

    # 3. Əgər heç biri cavab verməzsə, ən azı Mərkəzi Bankın günün rəsmi XML bazasını qeyd edirik
    if not rates_list:
        try:
            today_str = datetime.now().strftime("%d.%m.%Y")
            cbar_url = f"https://www.cbar.az/currencies/{today_str}.xml"
            cbar_resp = requests.get(cbar_url, headers=headers, timeout=10)
            if cbar_resp.status_code == 200:
                cbar_soup = BeautifulSoup(cbar_resp.content, "xml")
                for v in cbar_soup.find_all("Valute"):
                    code = v.get("Code")
                    if code in ["USD", "EUR", "RUB", "TRY", "GBP"]:
                        val = v.find("Value").text.replace(",", ".")
                        rates_list.append({
                            "bank": "Azərbaycan Mərkəzi Bankı",
                            "currency": code,
                            "cash_buy": val,
                            "cash_sell": val,
                            "cashless_buy": val,
                            "cashless_sell": val
                        })
        except Exception as e:
            print(f"CBAR xətası: {e}")

    result = {
        "success": True,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_records": len(rates_list),
        "rates": rates_list
    }

    with open("rates.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"rates.json yeniləndi. Ümumi qeyd: {len(rates_list)}")

if __name__ == "__main__":
    fetch_real_bank_rates()
