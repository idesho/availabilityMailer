#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
from datetime import datetime
import re
from utils import get_weekday_jp, is_weekend_or_holiday


# ───────────────────────────────
# 表示中の年月を取得（複数あれば最後を使う）
# ───────────────────────────────
def get_display_year_month(page_source: str):
    """
    HTML内の『空き室状況 xxxx年x月分』を全部拾って最後の (year, month) を返す。
    取れなければ (None, None)。
    """
    matches = re.findall(r"空き室状況[^0-9]*(\d{4})年(\d{1,2})月", page_source)
    if matches:
        y, m = matches[-1]  # 最後（=現在表示中と思われる）を採用
        return int(y), int(m)
    return None, None


# ───────────────────────────────
# ページロード待機 & HTML取得
# ───────────────────────────────
def check_availability(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/form/table[1]/tbody/tr[3]/td/table/tbody/tr/td[3]")
            )
        )
    except TimeoutException:
        print("ページの読み込みがタイムアウトしました。")
        return None
    return driver.page_source


# ───────────────────────────────
# HTML解析
# ───────────────────────────────
def parse_availability(page_source, current_year, current_month, id_range):
    soup = BeautifulSoup(page_source, 'html.parser')
    date_info = []

    first_raw_day = None      # その月で最初に見た raw day
    day_offset    = 0         # 0始まりなら 1 を足す

    for i in id_range:
        td = soup.find('td', id=f'right_v{i}')
        if not td:
            continue

        tr = td.find_parent('tr')
        if not tr:
            continue

        # 体育室判定はそのまま
        if isinstance(id_range, range):
            if id_range.start <= i < id_range.start + 4:
                gym_info = "体育室A"
            elif id_range.start + 4 <= i < id_range.start + 8:
                gym_info = "体育室B"
            elif id_range.start + 8 <= i < id_range.stop:
                gym_info = "体育室C"
            else:
                gym_info = ""
        else:
            idx = id_range.index(i)
            if idx < 4:
                gym_info = "手前"
            elif 4 <= idx < 8:
                gym_info = "中央"
            elif 8 <= idx < 12:
                gym_info = "奥"
            else:
                gym_info = ""

        time_slot = td.text.strip()

        for td_cell in tr.find_all('td'):
            onmouseover = td_cell.get('onmouseover')
            if not onmouseover:
                continue

            # できれば YYYY年M月D日 を直接取る（あれば最優先）
            m_full = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', onmouseover)
            if m_full:
                y, m, d = map(int, m_full.groups())
                date_str = f"{y}/{m:02}/{d:02}"
            else:
                # フォールバック: 最初の数字引数を day とみなす
                m_day = re.search(r'\((\d{1,2})[,)]', onmouseover)
                if not m_day:
                    continue

                raw_day = int(m_day.group(1))

                # 最初の raw_day 観測で 0 だったら 0始まりと判断
                if first_raw_day is None:
                    first_raw_day = raw_day
                    day_offset = 1 if raw_day == 0 else 0

                day = raw_day + day_offset
                if not (1 <= day <= 31):
                    continue

                date_str = f"{current_year}/{current_month:02}/{day:02}"

            # × or 黒塗りは除外
            style_attr = td_cell.get('style', '')
            if ('background-color:#333333' in style_attr) or ('×' in td_cell.text):
                continue

            weekday_jp = get_weekday_jp(date_str)
            date_info.append((date_str, weekday_jp, time_slot, gym_info))

    return sorted(date_info, key=lambda x: datetime.strptime(x[0], "%Y/%m/%d"))



# ───────────────────────────────
# 結果表示
# ───────────────────────────────
def display_results(date_info_sorted):
    today_dt = datetime.strptime(datetime.now().strftime("%Y/%m/%d"), "%Y/%m/%d")
    for date_str, weekday_jp, time_slot, gym_info in date_info_sorted:
        target_dt = datetime.strptime(date_str, "%Y/%m/%d")
        if target_dt >= today_dt and is_weekend_or_holiday(target_dt):
            print(f"{date_str} ({weekday_jp}) ({time_slot}: {gym_info})<br>")


# ───────────────────────────────
# メイン
# ───────────────────────────────
if __name__ == "__main__":
    centers = [
        {"url": "https://yokohama-shisetsu.com/yoyaku_test/wb_pub.php?sisetu_code=02",
         "range": range(8, 20), "name": "藤が丘地区センター"},
        {"url": "https://yokohama-shisetsu.com/yoyaku_test/wb_pub.php?sisetu_code=03",
         "range": range(0, 12), "name": "若草台地区センター"},
        {"url": "https://yokohama-shisetsu.com/yoyaku_test/wb_pub.php?sisetu_code=04",
         "range": range(0, 12), "name": "美しが丘西地区センター"},
        {"url": "https://yokohama-shisetsu.com/yoyaku_test/wb_pub.php?sisetu_code=05",
         "range": range(0, 12), "name": "奈良地区センター"},
        {"url": "https://f-supportsys.com/nisiku/yoyaku/wb_pub.php?sisetu_code=01",
         "range": list(range(0, 4)) + list(range(8, 12)) + list(range(16, 20)), "name": "藤棚地区センター"},
    ]

    options = Options()
    options.add_argument('--headless')  # 必要なら有効化
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')

    driver = webdriver.Chrome(options=options)

    try:
        for center in centers:
            print(f"<br>{center['name']}の空き状況<br>")
            driver.get(center["url"])

            seen_months = set()  # 重複防止

            while True:
                page_source = check_availability(driver)
                if not page_source:
                    break

                y, m = get_display_year_month(page_source)
                if y is None or m is None:
                    now = datetime.now()
                    y, m = now.year, now.month

                # デバッグ確認（必要なら）
                # print(f"{center['name']} -> {y}年{m}月解析中")

                if (y, m) in seen_months:
                    # 同じ月を再度取ってきた ⇒ これ以上進めない or 取得失敗
                    break
                seen_months.add((y, m))

                date_info_sorted = parse_availability(page_source, y, m, center["range"])
                display_results(date_info_sorted)

                # 次月へ
                try:
                    if center['name'] == "藤棚地区センター":
                        xpath = "/html/body/form/table[1]/tbody/tr[3]/td/table/tbody/tr/td[3]/span"
                        wait_xpath = "/html/body/form/table[1]/tbody/tr[3]/td/table/tbody/tr/td[3]"
                    else:
                        xpath = "/html/body/form/table[1]/tbody/tr[3]/td/table/tbody/tr/td[4]/span"
                        wait_xpath = "/html/body/form/table[1]/tbody/tr[3]/td/table/tbody/tr/td[4]"

                    prev_year_month = (y, m)

                    next_button = driver.find_element(By.XPATH, xpath)
                    next_button.click()

                    # 年月が変わるのを待つ
                    WebDriverWait(driver, 10).until(
                        lambda d: get_display_year_month(d.page_source) != prev_year_month
                    )

                    # 念のため対象セルの presence も確認
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, wait_xpath))
                    )

                except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                    break
    finally:
        driver.quit()
