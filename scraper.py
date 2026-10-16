import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
import cloudscraper

def get_html(url):
    """Bloklamanı keçmək üçün əvvəlcə Chrome TLS imzası (curl_cffi), alınmasa cloudscraper istifadə edir"""
    try:
        resp = cffi_requests.get(url, impersonate="chrome120", timeout=20)
        if resp.status_code == 200 and len(resp.text) > 500:
            return resp.text
        print(f"curl_cffi status {resp.status_code}: {url}")
    except Exception as e:
        print(f"curl_cffi xətası: {e}")

    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        resp = scraper.get(url, timeout=20)
        if resp.status_code == 200 and len(resp.text) > 500:
            return resp.text
        print(f"cloudscraper status {resp.status_code}: {url}")
    except Exception as e:
        print(f"cloudscraper xətası: {e}")

    return None

def parse_azn_day_az(html, currency):
    """azn.day.az səhifəsindən bütün bankları və nağd/nağdsız kursları çıxarır"""
    rates = []
    soup = BeautifulSoup(html, "html.parser")

    # 1-ci üsul: HTML cədvəl sətirləri (tr/td) ilə
    for tr in soup.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if len(tds) >= 5:
            bank = tds[0]
            c_buy, c_sell, nc_buy, nc_sell = tds[1], tds[2], tds[3], tds[4]

            if any(skip in bank for skip in ["Bankın adı", "Bank", "Valyuta", "Currency"]):
                continue

            # Rəqəm formatını yoxlayırıq (məs: 1.6970 və ya -)
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

def parse_kredit_az(html):
    """Əgər azn.day.az bloklanarsa, kredit.az-dan real nağd/nağdsız kursları çıxarır"""
    rates = []
    soup = BeautifulSoup(html, "html.parser")
    for tr in soup.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(tds) >= 5:
            bank_raw = tds[0].split()
            bank = " ".join(bank_raw[:len(bank_raw)//2]) if len(bank_raw) >= 2 else tds[0]
            c_buy, c_sell, nc_buy, nc_sell = tds[1], tds[2], tds[3], tds[4]
            if re.search(r'\d+\.\d+', f"{c_buy} {c_sell}"):
                rates.append({
                    "bank": bank,
                    "currency": "USD",
                    "cash_buy": c_buy,
                    "cash_sell": c_sell,
                    "cashless_buy": nc_buy,
                    "cashless_sell": nc_sell
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

    for currency, url in urls.items():
        html = get_html(url)
        if html:
            extracted = parse_azn_day_az(html, currency)
            print(f"{currency} üçün azn.day.az-dan {len(extracted)} bank tapıldı.")
            rates_list.extend(extracted)
        else:
            print(f"{currency} üçün HTML alına bilmədi.")

    # Əgər azn.day.az xarici IP-ni tam bloklayıbsa, kredit.az-ı yoxlayırıq
    if not rates_list:
        print("Alternativ mənbə (kredit.az) yoxlanılır...")
        html_alt = get_html("https://kredit.az/kalkulyator/valyuta")
        if html_alt:
            rates_list.extend(parse_kredit_az(html_alt))

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
