# 必要なモジュールをインポート
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
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
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920x1080')

# URLリストの定義
urls = {
    '白幡': "https://shirahatac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
}

# 各URLについて処理を行う関数
def process_url(area, url):
    try:
        logging.info(f"{area} の処理を開始します。URL: {url}")
        driver = webdriver.Chrome(options=options)

        driver.get(url)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "serch_btn"))).click()
        results = [f"<br>{area}地区センターの空き状況<br>"]

        while True:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            td_elements = soup.find_all('td')
            results.extend([f"{td.get('title')}<br>" for td in td_elements if td.get('title')])

            try:
                next_link = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#next a")))
                driver.execute_script("arguments[0].click();", next_link)
            except Exception:
                break

        driver.quit()
        return ''.join(results)

    except Exception as e:
        logging.error(f"{area} の処理中にエラーが発生しました: {e}")
        logging.debug(traceback.format_exc())
        return f"{area} の処理中にエラーが発生しました。"

# メイン処理
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
        futures = {executor.submit(process_url, area, url): area for area, url in urls.items()}
        results = {futures[future]: future.result() for future in concurrent.futures.as_completed(futures)}

    for area, result in results.items():
        print(result)
except Exception as e:
    logging.error(f"全体の処理中にエラーが発生しました: {e}")
    logging.debug(traceback.format_exc())
