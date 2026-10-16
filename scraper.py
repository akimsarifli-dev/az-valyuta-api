import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_real_rates():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "az,en-US;q=0.9,en;q=0.8"
    }

    # Hər valyutanın canlı cədvəl ünvanı
    urls = {
        "USD": "https://azn.day.az/az/",
        "EUR": "https://azn.day.az/az/rates/eur",
        "RUB": "https://azn.day.az/az/rates/rub",
        "TRY": "https://azn.day.az/az/rates/try",
        "GBP": "https://azn.day.az/az/rates/gbp"
    }

    rates_list = []

    for currency, url in urls.items():
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"{currency} səhifəsi açılmadı, status: {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Səhifədəki bütün cədvəl sətirlərini (tr) yoxlayırıq
            for tr in soup.find_all("tr"):
                tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                
                # Cədvəl strukturu: [Bankın adı, Nağd Alış, Nağd Satış, Nağdsız Alış, Nağdsız Satış, Telefon]
                if len(tds) >= 5:
                    bank_name = tds[0]
                    cash_buy = tds[1]
                    cash_sell = tds[2]
                    cashless_buy = tds[3]
                    cashless_sell = tds[4]

                    # Başlıq sətirlərini və valyuta olmayan sətirləri keçirik
                    if not bank_name or "Bankın adı" in bank_name or "Valyuta" in bank_name:
                        continue

                    # Ən azı bir məzənnədə rəqəm və nöqtə varsa (məs: 1.6970), siyahıya əlavə edirik
                    has_valid_rate = any("." in val for val in [cash_buy, cash_sell, cashless_buy, cashless_sell])
                    if has_valid_rate:
                        rates_list.append({
                            "bank": bank_name,
                            "currency": currency,
                            "cash_buy": cash_buy if cash_buy else "-",
                            "cash_sell": cash_sell if cash_sell else "-",
                            "cashless_buy": cashless_buy if cashless_buy else "-",
                            "cashless_sell": cashless_sell if cashless_sell else "-"
                        })
        except Exception as e:
            print(f"{currency} oxunarkən xəta: {e}")

    result = {
        "success": len(rates_list) > 0,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_records": len(rates_list),
        "rates": rates_list
    }

    with open("rates.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Tamamlandı! Cəmi çəkilən real bank kursu: {len(rates_list)}")

if __name__ == "__main__":
    fetch_real_rates()
