import json
import re
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

def get_via_proxy(target_url):
    """GitHub IP blokunu (403) keçmək üçün açıq proksi servislərindən istifadə edir"""
    proxies = [
        f"https://api.codetabs.com/v1/proxy?quest={urllib.parse.quote(target_url)}",
        f"https://api.allorigins.win/raw?url={urllib.parse.quote(target_url)}",
        target_url  # Birbaşa (kredit.az və banco.az üçün)
    ]

    for p_url in proxies:
        try:
            resp = cffi_requests.get(p_url, impersonate="chrome120", timeout=25)
            if resp.status_code == 200 and len(resp.text) > 1000:
                # Əgər səhifədə bank adları varsa, uğurludur
                if any(b in resp.text for b in ["Kapital", "ABB", "Unibank", "Respublika", "Pasha", "Paşa"]):
                    print(f"Uğurla oxundu: {p_url[:45]}...")
                    return resp.text
        except Exception as e:
            print(f"Sorğu xətası ({p_url[:35]}): {e}")
    return None

def parse_azn_day_az(html, currency):
    """azn.day.az cədvəlini oxuyur"""
    rates = []
    soup = BeautifulSoup(html, "html.parser")

    for tr in soup.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if len(tds) >= 5:
            bank = tds[0]
            c_buy, c_sell, nc_buy, nc_sell = tds[1], tds[2], tds[3], tds[4]

            if any(skip in bank for skip in ["Bankın adı", "Bank", "Valyuta", "Currency", "MMC", "LLC"]):
                continue

            if re.search(r'\d+\.\d+', f"{c_buy} {c_sell} {nc_buy} {nc_sell}"):
                rates.append({
                    "bank": bank,
                    "currency": currency,
                    "cash_buy": c_buy if re.search(r'\d+\.\d+', c_buy) else "-",
                    "cash_sell": c_sell if re.search(r'\d+\.\d+', c_sell) else "-",
                    "cashless_buy": nc_buy if re.search(r'\d+\.\d+', nc_buy) else "-",
                    "cashless_sell": nc_sell if re.search(r'\d+\.\d+', nc_sell) else "-"
                })
    return rates

def parse_kredit_az_full(html):
    """Bloklanmayan kredit.az səhifəsindən bütün bankları və nağd/nağdsız kursları çıxarır"""
    rates = []
    soup = BeautifulSoup(html, "html.parser")
    text_content = soup.get_text(" ", strip=True)

    known_banks = [
        "birbank", "ABB", "Rabitəbank", "Unibank", "AccessBank",
        "Bank Respublika", "Bank of Baku", "Yapı Kredi Bank Azərbaycan",
        "Premium Bank", "TuranBank", "Kapital Bank", "PAŞA Bank", "Yelo Bank", "Xalq Bank"
    ]

    # Səhifədəki mətn strukturundan (Bank + 4 rəqəm: Nağd Alış, Nağd Satış, Nağdsız Alış, Nağdsız Satış)
    for bank in known_banks:
        pattern = rf"{re.escape(bank)}(?:\s+{re.escape(bank)})?\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)"
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            display_name = "Kapital Bank (Birbank)" if bank.lower() == "birbank" else bank
            rates.append({
                "bank": display_name,
                "currency": "USD",
                "cash_buy": match.group(1),
                "cash_sell": match.group(2),
                "cashless_buy": match.group(3),
                "cashless_sell": match.group(4)
            })
    return rates

def parse_banco_az(html):
    """Bloklanmayan banco.az səhifəsindən USD və EUR kurslarını çıxarır"""
    rates = []
    soup = BeautifulSoup(html, "html.parser")
    text_content = soup.get_text(" ", strip=True)

    # Banco.az formatı: Bank adı ... USD - Доллар СШA 1.6980 1.7020 EUR - Евро 1.9060 1.9346
    pattern = r"([A-Za-zƏəÖöÜüĞğÇçŞşİı\s]+?)\s+Покупка\s+Продажа\s+USD\s*-\s*Доллар\s*СШA\s+(\d+\.\d+)\s+(\d+\.\d+)\s+EUR\s*-\s*Евро\s+(\d+\.\d+)\s+(\d+\.\d+)"
    for m in re.finditer(pattern, text_content):
        bank = m.group(1).strip()
        if len(bank) > 2:
            rates.append({
                "bank": bank,
                "currency": "USD",
                "cash_buy": m.group(2),
                "cash_sell": m.group(3),
                "cashless_buy": m.group(2),
                "cashless_sell": m.group(3)
            })
            rates.append({
                "bank": bank,
                "currency": "EUR",
                "cash_buy": m.group(4),
                "cash_sell": m.group(5),
                "cashless_buy": m.group(4),
                "cashless_sell": m.group(5)
            })
    return rates

def fetch_real_rates():
    urls = {
        "USD": "https://azn.day.az/az/",
        "EUR": "https://azn.day.az/az/rates/eur",
        "RUB": "https://azn.day.az/az/rates/rub",
        "TRY": "https://azn.day.az/az/rates/try",
        "GBP": "https://azn.day.az/az/rates/gbp"
    }

    rates_list = []

    # 1. Proksi üzərindən azn.day.az (bütün valyutalar və nağd/nağdsız)
    for currency, url in urls.items():
        html = get_via_proxy(url)
        if html:
            extracted = parse_azn_day_az(html, currency)
            print(f"{currency} üçün azn.day.az-dan {len(extracted)} bank tapıldı.")
            rates_list.extend(extracted)

    # 2. Əgər proksi də cavab verməzsə, birbaşa kredit.az (GitHub-ı bloklamır!)
    if not rates_list:
        print("Birbaşa kredit.az oxunur...")
        html_kredit = get_via_proxy("https://kredit.az/kalkulyator/valyuta")
        if html_kredit:
            extracted = parse_kredit_az_full(html_kredit)
            print(f"kredit.az-dan {len(extracted)} bank tapıldı.")
            rates_list.extend(extracted)

    # 3. Əlavə olaraq birbaşa banco.az (GitHub-ı bloklamır!)
    if len(rates_list) < 15:
        print("Birbaşa banco.az oxunur...")
        html_banco = get_via_proxy("https://banco.az/ru/bank-azn-courses")
        if html_banco:
            extracted = parse_banco_az(html_banco)
            print(f"banco.az-dan {len(extracted)} qeyd tapıldı.")
            rates_list.extend(extracted)

    result = {
        "success": len(rates_list) > 0,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_records": len(rates_list),
        "rates": rates_list
    }

    with open("rates.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Yekunlaşdı! Cəmi qeyd: {len(rates_list)}")

if __name__ == "__main__":
    fetch_real_rates()
