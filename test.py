from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import concurrent.futures
from utils import get_weekday_jp, is_weekend_or_holiday

# Chromeのオプションを設定
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')  # 必要に応じて追加
options.add_argument('--window-size=1920,1080')  # PC表示にする(区切りはカンマ)

# 複数のURLをリストで定義
urls = {
    '白幡': "https://shirahata.actio-shisetsu-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    '矢向': "https://yako.npo-ttk-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    '潮田': "https://ushioda.npo-ttk-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    '寺尾': "https://terao.npo-ttk-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    '生麦': "https://namamugi.npo-ttk-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    '末吉': "https://sueyoshi.npo-ttk-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    # '長津田': "https://nagatsuta.npo-ttk-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    "中川西": "https://tsuzukikoryu-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    "仲町台":"https://tsuzukikoryu-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=02",
    "北山田": "https://tsuzukikoryu-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=03",
    "中山":"https://m-shisetsu-kyokai-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01",
    "都築":"https://tsuzukicenter-nexres.com/nexres/KR/KSR0100/index.php?mokuteki=01"
}

# 各URLについて処理を行う関数
def process_url(area, url):
    # Selenium WebDriverの初期化
    driver = webdriver.Chrome(options=options)
    # 指定されたURLにアクセス
    driver.get(url)

    # 月別ボタンがクリック可能になるまで待機
    button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class,'serch_btn') and normalize-space()='月別']")))
    driver.execute_script("arguments[0].click();", button)

    results = [f"<br>{area}地区センターの空き状況<br>"]
    
    while True:
        # 現在のページのデータを取得
        html_current = driver.page_source
        soup = BeautifulSoup(html_current, 'html.parser')
        # td要素をすべて取得する
        td_elements = soup.find_all('td')

        # タイトルを月日の昇順でソートするためのキー関数
        def sort_key(title):
            if title:
                parts = title.split(' ')[0].split('/')
                return int(parts[1]), int(parts[2])
            else:
                return (0, 0)

        # 各td要素について処理を行う
        for td_element in sorted(td_elements, key=lambda x: sort_key(x.get('title'))):
            # td要素からtitle属性を取得
            title = td_element.get('title')

            # title属性が存在する場合のみ処理を行う
            if title and '体育室' in title and td_element.get_text(strip=True) == '〇':
                # title属性の値を日付オブジェクトに変換
                date_str = title.split(' ')[0]
                date_obj = datetime.strptime(date_str, "%Y/%m/%d")

                weekday_jp = get_weekday_jp(date_obj)

                # 土曜日、日曜日の場合のみ出力する
                if is_weekend_or_holiday(date_obj):
                # if "夜間Ⅱ" in title:
                    results.append(f"{title} ({weekday_jp})<br>")

        # 次のページへのリンクをクリック
        try:
            next_link = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#next a")))
            driver.execute_script("arguments[0].click();", next_link)
        except:
            break

    # ブラウザを閉じる
    driver.quit()

    return ''.join(results)

# マルチスレッドでURLを処理し、順番に結果を表示
with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
    # futureオブジェクトとエリア名を紐付けて管理
    futures = {executor.submit(process_url, area, url): area for area, url in urls.items()}
    results = {area: future.result() for future, area in zip(futures.keys(), futures.values())}

# 結果を指定された順序で表示
for area in urls.keys():
    print(results[area])