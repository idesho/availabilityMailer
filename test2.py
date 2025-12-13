#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
横浜市 NexRes 各地区センターの体育室空き状況（土日祝）を取得し、
HTML 文字列として返すモジュールスクリプト。

使い方:
    python3 test2.py          # 結果を標準出力
    from test2 import scrape  # 関数呼び出しで文字列取得

CI(GitHub Actions)向け:
    - MAX_WORKERS=1 を推奨（Chrome同時起動は不安定になりがち）
    - HEADLESS=0 で xvfb-run 実行も可能（headless弾き対策）
"""

from __future__ import annotations

from datetime import datetime
import concurrent.futures
import logging
import os
import time
import traceback

import jpholiday
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException,
)

# ────────────────────────────────────────────────
# 1. 設定
# ────────────────────────────────────────────────
URLS: dict[str, str] = {
    "白幡": "https://shirahatac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "矢向": "https://yakoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "潮田": "https://ushiodac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "寺尾": "https://teraoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "生麦": "https://namamugic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "末吉": "https://sueyoshic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "長津田": "https://nagatsutac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "中川西": "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "仲町台": "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=02",
    "北山田": "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=03",
    "中山": "https://nakayamac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    "都筑": "https://tsuzuki-center-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
}

# CIでは MAX_WORKERS=1 推奨（Chrome複数同時起動は落ちやすい）
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# HEADLESS=1(デフォルト) / HEADLESS=0(非headless)
HEADLESS = os.getenv("HEADLESS", "1") == "1"

# dump 出力先
DUMP_DIR = os.getenv("DUMP_DIR", "dump")

# ────────────────────────────────────────────────
# 2. 共通ユーティリティ
# ────────────────────────────────────────────────
JP_WEEKDAY = dict(
    zip(
        ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
        ("月", "火", "水", "木", "金", "土", "日"),
    )
)

def create_driver() -> webdriver.Chrome:
    """CIでも比較的安定するChrome設定で driver を作成."""
    options = Options()

    if HEADLESS:
        # GitHub Actionsでは --headless=new の方が安定しやすいことがある
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ja-JP")

    # 多少効くことがある“自動化っぽさ”軽減（効かないサイトもある）
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # いかにもcurl/headlessっぽいのを避けるUA
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    return driver

def sort_key(title: str | None) -> tuple[int, int]:
    """title='YYYY/MM/DD ...' → (MM, DD)"""
    if not title:
        return (0, 0)
    parts = title.split(" ")[0].split("/")
    return int(parts[1]), int(parts[2])

def wait_dom_ready(driver: webdriver.Chrome, timeout: int = 20) -> None:
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def dump(driver: webdriver.Chrome, area: str, tag: str) -> None:
    """失敗時の画面/HTML/URL/タイトルを必ず残す（Actionsのartifactで回収する用）"""
    try:
        os.makedirs(DUMP_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        base = os.path.join(DUMP_DIR, f"{ts}_{area}_{tag}")

        # screenshot
        try:
            driver.save_screenshot(base + ".png")
        except Exception:
            pass

        # html
        try:
            with open(base + ".html", "w", encoding="utf-8") as f:
                f.write(driver.page_source or "")
        except Exception:
            pass

        # meta
        try:
            with open(base + ".txt", "w", encoding="utf-8") as f:
                f.write(f"url={getattr(driver, 'current_url', '')}\n")
                f.write(f"title={getattr(driver, 'title', '')}\n")
        except Exception:
            pass
    except Exception:
        # dumpの失敗は本筋じゃないので握りつぶす
        pass

# ────────────────────────────────────────────────
# 3. メイン処理
# ────────────────────────────────────────────────
def scrape_one(area: str, url: str) -> str:
    """1施設ぶんを取得して HTML 文字列で返す."""
    logging.info("start scraping: %s", area)
    driver = create_driver()
    try:
        driver.get(url)
        wait_dom_ready(driver, timeout=25)

        # 「月別」検索ボタン（serch_btn）をクリック
        try:
            btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "serch_btn"))
            )
        except Exception as e:
            # ここで落ちる = CIでは別ページ(404/ブロック/注意)の可能性が高い
            dump(driver, area, "wait_serch_btn_failed")
            raise RuntimeError(
                f"{area}: serch_btn not found/clickable. "
                f"url={driver.current_url} title={driver.title} exc={type(e).__name__}"
            ) from e

        # クリック（通常clickが効かない時もあるのでJS）
        try:
            driver.execute_script("arguments[0].click();", btn)
        except Exception as e:
            dump(driver, area, "click_serch_btn_failed")
            raise RuntimeError(
                f"{area}: failed to click serch_btn. "
                f"url={driver.current_url} title={driver.title} exc={type(e).__name__}"
            ) from e

        # クリック後の描画待ち（ページソース変化 or tdが出るまで）
        before = driver.page_source
        try:
            WebDriverWait(driver, 20).until(
                lambda d: d.page_source != before
                or "title=" in (d.page_source or "")
            )
        except Exception:
            # 変化しない場合もあるので続行はするが、後段で拾えなければdumpへ
            pass

        lines: list[str] = [f"<br><b>{area}地区センターの空き状況</b><br>"]

        max_pages = 24  # 念のため無限ループ防止
        for _ in range(max_pages):
            soup = BeautifulSoup(driver.page_source, "html.parser")

            found_any = False
            for td in sorted(soup.find_all("td"), key=lambda t: sort_key(t.get("title"))):
                title = td.get("title")
                if title and "体育室" in title and td.get_text(strip=True) == "〇":
                    date_str = title.split()[0]  # 'YYYY/MM/DD'
                    dt = datetime.strptime(date_str, "%Y/%m/%d")
                    weekday = "祝" if jpholiday.is_holiday(dt) else JP_WEEKDAY[dt.strftime("%A")]
                    if weekday in ("土", "日", "祝"):
                        found_any = True
                        lines.append(f"{title}（{weekday}）<br>")

            # 次ページへ（存在しなければ終了）
            try:
                # next が無い施設もあるので短め
                next_a = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#next a"))
                )
            except TimeoutException:
                break

            # クリックしてページが変わらなければ終わり（disabled扱い）
            old = driver.page_source
            try:
                driver.execute_script("arguments[0].click();", next_a)
                WebDriverWait(driver, 10).until(lambda d: d.page_source != old)
            except (TimeoutException, StaleElementReferenceException):
                break
            except WebDriverException:
                break

        logging.info("scrape success: %s", area)
        return "".join(lines)

    except Exception:
        # 施設単位での失敗はここでdumpを残す（上で残してなければ）
        dump(driver, area, "unexpected_error")
        raise
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def scrape() -> str:
    """全施設まとめて実行し、HTML を返す."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results: dict[str, str] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_to_area = {ex.submit(scrape_one, area, url): area for area, url in URLS.items()}

        for fut in concurrent.futures.as_completed(fut_to_area):
            area = fut_to_area[fut]
            try:
                results[area] = fut.result()
            except Exception as exc:
                # 「Message: Stacktrace」だけになるのを避けて、例外タイプも表示する
                logging.exception("scrape failed: %s", area)
                results[area] = (
                    f"<br><b>{area}地区センターの空き状況</b><br>"
                    f"取得失敗: {type(exc).__name__}: {exc}<br>"
                )

    # 表示順は URLS の並びを維持
    return "".join(results[area] for area in URLS.keys())


if __name__ == "__main__":
    print(scrape())
