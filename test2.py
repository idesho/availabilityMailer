# 必要なモジュールをインポート
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import logging
import traceback

# ログ設定
logging.basicConfig(
    filename="test_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Chromeのオプションを設定（ヘッドレスモード）
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

        # Selenium WebDriverを起動
        driver = webdriver.Chrome(options=options)

        # URL にアクセス
        logging.info(f"{area} - URL にアクセス中。")
        driver.get(url)

        # ボタンのクリック
        try:
            logging.info(f"{area} - ボタンを探しています。")
            button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "serch_btn")))
            button.click()
            logging.info(f"{area} - ボタンをクリックしました。")
        except Exception as e:
            logging.error(f"{area} - ボタンが見つからない、またはクリックに失敗しました: {e}")
            raise

        results = [f"<br>{area}地区センターの空き状況<br>"]

        # ページ処理のループ
        while True:
            html_current = driver.page_source
            soup = BeautifulSoup(html_current, 'html.parser')
            td_elements = soup.find_all('td')

            logging.info(f"{area} - ページ内のテーブルデータ数: {len(td_elements)}")
            for td_element in td_elements:
                title = td_element.get('title')
                if title:
                    results.append(f"{title}<br>")

            # 次ページへ
            try:
                next_link = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#next a")))
                driver.execute_script("arguments[0].click();", next_link)
                logging.info(f"{area} - 次ページに移動しました。")
            except Exception as e:
                logging.info(f"{area} - 次ページが見つからないか、移動できません: {e}")
                break

        # ブラウザを閉じる
        driver.quit()
        logging.info(f"{area} の処理が正常に完了しました。")
        return ''.join(results)

    except Exception as e:
        logging.error(f"{area} の処理中にエラーが発生しました: {e}")
        logging.debug(traceback.format_exc())
        return f"{area} の処理中にエラーが発生しました。"

# メイン処理
try:
    results = {}
    for area, url in urls.items():
        results[area] = process_url(area, url)

    for area, result in results.items():
        print(result)
except Exception as main_e:
    logging.error(f"全体の処理中にエラーが発生しました: {main_e}")
    logging.debug(traceback.format_exc())
