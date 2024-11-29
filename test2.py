# 必要なモジュールをインポート
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import jpholiday
import concurrent.futures
import logging
import traceback

# ログ設定
logging.basicConfig(
    filename="test_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Chromeのオプションを設定
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')  # 必要に応じて追加
options.add_argument('--window-size=1920x1080')  # 必要に応じて追加

# URLリストの定義
urls = {
    '白幡': "https://shirahatac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    # '矢向': "https://yakoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    # '潮田': "https://ushiodac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    # '寺尾': "https://teraoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    # '生麦': "https://namamugic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    # '末吉': "https://sueyoshic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    # '長津田': "https://nagatsutac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    # "中川西": "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    # "仲町台":"https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=02",
    # "北山田": "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=03",
    # "中山":"https://nakayamac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
} 

# 各URLについて処理を行う関数
def process_url(area, url):
    try:
        logging.info(f"{area} の処理を開始します。")
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # ボタンのクリック
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "serch_btn")))
        button.click()

        results = [f"<br>{area}地区センターの空き状況<br>"]
        
        # ページ処理のループ
        while True:
            html_current = driver.page_source
            soup = BeautifulSoup(html_current, 'html.parser')
            td_elements = soup.find_all('td')

            # td要素の処理
            for td_element in td_elements:
                title = td_element.get('title')
                if title:
                    results.append(f"{title}<br>")

            # 次ページへ
            try:
                next_link = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#next a")))
                driver.execute_script("arguments[0].click();", next_link)
            except:
                break

        driver.quit()
        logging.info(f"{area} の処理が完了しました。")
        return ''.join(results)

    except Exception as e:
        logging.error(f"{area} の処理中にエラーが発生しました: {e}")
        logging.debug(traceback.format_exc())
        return f"{area} の処理中にエラーが発生しました。"

# メイン処理
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
        futures = {executor.submit(process_url, area, url): area for area, url in urls.items()}
        results = {}
        for future in concurrent.futures.as_completed(futures):
            area = futures[future]
            try:
                results[area] = future.result()
            except Exception as e:
                logging.error(f"{area} の結果取得中にエラー: {e}")

    for area in urls.keys():
        print(results.get(area, f"{area}: データ取得に失敗しました"))
except Exception as main_e:
    logging.error(f"全体の処理中にエラーが発生しました: {main_e}")
    logging.debug(traceback.format_exc())
