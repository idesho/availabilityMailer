# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup
# from datetime import datetime
# import jpholiday
# import concurrent.futures

# # Chromeのオプションを設定
# options = Options()
# options.add_argument('--headless')
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--disable-gpu')  # 必要に応じて追加
# options.add_argument('--window-size=1920x1080')  # 必要に応じて追加

# # 複数のURLをリストで定義
# urls = {
#     '白幡': "https://shirahatac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     '矢向': "https://yakoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     '潮田': "https://ushiodac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     '寺尾': "https://teraoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     '生麦': "https://namamugic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     '末吉': "https://sueyoshic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     '長津田': "https://nagatsutac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     "中川西": "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     "仲町台":"https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=02",
#     "北山田": "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=03",
#     "中山":"https://nakayamac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
#     "都築":"https://tsuzuki-center-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01"
# }

# # 各URLについて処理を行う関数
# def process_url(area, url):
#     # Selenium WebDriverの初期化
#     driver = webdriver.Chrome(options=options)
#     # 指定されたURLにアクセス
#     driver.get(url)

#     # 月別ボタンがクリック可能になるまで待機
#     button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "serch_btn")))
#     button.click()

#     results = [f"<br>{area}地区センターの空き状況<br>"]
    
#     while True:
#         # 現在のページのデータを取得
#         html_current = driver.page_source
#         soup = BeautifulSoup(html_current, 'html.parser')
#         # td要素をすべて取得する
#         td_elements = soup.find_all('td')

#         # タイトルを月日の昇順でソートするためのキー関数
#         def sort_key(title):
#             if title:
#                 parts = title.split(' ')[0].split('/')
#                 return int(parts[1]), int(parts[2])
#             else:
#                 return (0, 0)

#         # 各td要素について処理を行う
#         for td_element in sorted(td_elements, key=lambda x: sort_key(x.get('title'))):
#             # td要素からtitle属性を取得
#             title = td_element.get('title')

#             # title属性が存在する場合のみ処理を行う
#             if title and '体育室' in title and td_element.get_text(strip=True) == '〇':
#                 # title属性の値を日付オブジェクトに変換
#                 date_str = title.split(' ')[0]
#                 date_obj = datetime.strptime(date_str, "%Y/%m/%d")

#                 # 祝日の場合は曜日の部分を「祝」とする
#                 if jpholiday.is_holiday(date_obj):
#                     weekday_jp = "祝"
#                 else:
#                     # 曜日を日本語で取得
#                     weekday_str = date_obj.strftime("%A")
#                     weekday_jp = {
#                         "Monday": "月",
#                         "Tuesday": "火",
#                         "Wednesday": "水",
#                         "Thursday": "木",
#                         "Friday": "金",
#                         "Saturday": "土",
#                         "Sunday": "日"
#                     }[weekday_str]

#                 # 土曜日、日曜日の場合のみ出力する
#                 if weekday_jp in ["土", "日", "祝"]:
#                 # if "夜間Ⅱ" in title:
#                     results.append(f"{title} ({weekday_jp})<br>")

#         # 次のページへのリンクをクリック
#         try:
#             next_link = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#next a")))
#             driver.execute_script("arguments[0].click();", next_link)
#         except:
#             break

#     # ブラウザを閉じる
#     driver.quit()

#     return ''.join(results)

# # マルチスレッドでURLを処理し、順番に結果を表示
# with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
#     # futureオブジェクトとエリア名を紐付けて管理
#     futures = {executor.submit(process_url, area, url): area for area, url in urls.items()}
#     results = {area: future.result() for future, area in zip(futures.keys(), futures.values())}

# # 結果を指定された順序で表示
# for area in urls.keys():
#     print(results[area])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
横浜市 NexRes 各地区センターの体育室空き状況（土日祝）を取得し、
HTML 文字列として返すモジュールスクリプト。

使い方:
    python3 test.py          # 結果を標準出力
    from test import scrape  # 関数呼び出しで文字列取得
"""
from __future__ import annotations
from datetime import datetime
import concurrent.futures
import jpholiday
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ────────────────────────────────────────────────
# 1. 設定  ─────────────────────────────────────────
# ────────────────────────────────────────────────
URLS: dict[str, str] = {
    '白幡': "https://shirahatac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '矢向': "https://yakoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '潮田': "https://ushiodac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '寺尾': "https://teraoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '生麦': "https://namamugic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '末吉': "https://sueyoshic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '長津田': "https://nagatsutac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '中川西': "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '仲町台': "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=02",
    '北山田': "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=03",
    '中山':   "https://nakayamac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '都筑':   "https://tsuzuki-center-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
}

MAX_WORKERS = 4  # Chrome 同時起動数 (リソース節約)

# ────────────────────────────────────────────────
# 2. 共通ユーティリティ  ───────────────────────────
# ────────────────────────────────────────────────
JP_WEEKDAY = dict(zip(
    ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    ("月", "火", "水", "木", "金", "土", "日"),
))

def create_driver() -> webdriver.Chrome:
    """新ヘッドレス & UA 偽装で driver 作成."""
    opts = Options()
    opts.add_argument("--headless=new")          # 新ヘッドレス
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=opts)

def sort_key(title: str | None) -> tuple[int, int]:
    """title='YYYY/MM/DD ...' → (MM, DD)"""
    if not title:
        return (0, 0)
    parts = title.split(' ')[0].split('/')
    return int(parts[1]), int(parts[2])

# ────────────────────────────────────────────────
# 3. メイン処理  ────────────────────────────────────
# ────────────────────────────────────────────────
def scrape_one(area: str, url: str) -> str:
    """1 施設ぶんを取得して HTML 文字列で返す."""
    driver = create_driver()
    try:
        driver.get(url)

        # 月別ボタンを JS クリック
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "serch_btn"))
        )
        driver.execute_script("arguments[0].click();", btn)

        lines: list[str] = [f"<br><b>{area}地区センターの空き状況</b><br>"]

        while True:
            soup = BeautifulSoup(driver.page_source, "html.parser")

            for td in sorted(soup.find_all("td"), key=lambda t: sort_key(t.get("title"))):
                title = td.get("title")
                if title and "体育室" in title and td.get_text(strip=True) == "〇":
                    date_str = title.split()[0]  # 'YYYY/MM/DD'
                    dt = datetime.strptime(date_str, "%Y/%m/%d")
                    weekday = "祝" if jpholiday.is_holiday(dt) else JP_WEEKDAY[dt.strftime("%A")]
                    if weekday in ("土", "日", "祝"):
                        lines.append(f"{title}（{weekday}）<br>")

            # 次ページへ
            try:
                next_link = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#next a"))
                )
                driver.execute_script("arguments[0].click();", next_link)
            except Exception:
                break

        return "".join(lines)

    finally:
        driver.quit()


def scrape() -> str:
    """全施設まとめて実行し、HTML を返す."""
    results: dict[str, str] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_to_area = {ex.submit(scrape_one, area, url): area for area, url in URLS.items()}
        for fut in concurrent.futures.as_completed(fut_to_area):
            area = fut_to_area[fut]
            results[area] = fut.result()

    # 表示順は URLS の並びを維持
    return "".join(results[area] for area in URLS.keys())


if __name__ == "__main__":
    # 単体テスト用途
    print(scrape())
