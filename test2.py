from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

def process_url(url):
    """指定されたURLを処理し、検索ボタンをクリック"""
    # ChromeDriverのオプション設定
    options = Options()
    # Headlessモード解除（デバッグ用）
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-gpu")

    # ChromeDriverサービスの初期化
    service = Service('/usr/bin/chromedriver')  # 適切なChromeDriverのパスに置き換えてください
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"URLにアクセス中: {url}")
        driver.get(url)

        # ページソースを保存（デバッグ用）
        with open("shirahatac_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # 検索ボタンがロードされるまで待機してクリック
        print("検索ボタンを探しています...")
        try:
            button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "serch_btn"))
            )
            print("検索ボタンをクリックします。")
            button.click()
        except Exception as e:
            print(f"ボタンが見つからない、またはクリックに失敗しました: {e}")
            # JavaScriptを使った代替クリック
            print("JavaScriptを使用してボタンを探します...")
            button = driver.execute_script("return document.querySelector('.serch_btn')")
            if button:
                driver.execute_script("arguments[0].click();", button)
                print("JavaScriptでボタンをクリックしました。")
            else:
                print("JavaScriptでもボタンが見つかりませんでした。")
    except Exception as main_error:
        print(f"処理中にエラーが発生しました: {main_error}")
    finally:
        print("ブラウザを閉じます。")
        driver.quit()

# メイン処理
if __name__ == "__main__":
    target_url = "https://shirahatac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01"
    process_url(target_url)
