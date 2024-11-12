from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import jpholiday
import concurrent.futures

# Chromeのオプションを設定
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920x1080')

# 各地区センターのURLとXPathリストを定義
urls = {
    '西': {
        "url": "https://nishic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
        "xpath_list": [
            ("/html/body/div[3]/div[3]/div[5]/table/tbody/tr/td[2]/div/table/tbody/tr[9]", "入口側"),
            ("/html/body/div[3]/div[3]/div[5]/table/tbody/tr/td[2]/div/table/tbody/tr[10]", "中央"),
            ("/html/body/div[3]/div[3]/div[5]/table/tbody/tr/td[2]/div/table/tbody/tr[12]", "倉庫側")
        ]
    },
    '十日市場': {
        "url": "https://tokaichibac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
        "xpath_list": [
            ("/html/body/div[3]/div[3]/div[5]/table/tbody/tr/td[2]/div/table/tbody/tr[3]", "奥"),
            ("/html/body/div[3]/div[3]/div[5]/table/tbody/tr/td[2]/div/table/tbody/tr[4]", "中央"),
            ("/html/body/div[3]/div[3]/div[5]/table/tbody/tr/td[2]/div/table/tbody/tr[5]", "手前")
        ]
    }
}

# 各URLについて処理を行う関数
def process_url(area, url_info):
    url = url_info["url"]
    xpath_list = url_info["xpath_list"]
    
    # Selenium WebDriverの初期化
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # 月別ボタンがクリック可能になるまで待機してクリック
    button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "serch_btn")))
    button.click()

    # 空き状況データを保存するリスト
    results = [f"<br>{area}地区センターの空き状況<br>"]  # 地区名のヘッダーを追加
    availability_list = []

    # 初回の処理日を今日の日付に設定
    current_date = datetime.today()

    # next_month_button が存在する限りループ
    while True:
        time_slots = ["午前", "午後1", "午後2", "夜間"]

        # 各XPathをループして処理
        for xpath, location in xpath_list:
            # 各場所ごとに日付をリセット
            day_date = current_date
            current_month = day_date.month  # 現在の月を保持

            # 指定のXPathで要素を取得
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )

            # BeautifulSoupで解析可能な形式に変換
            html_current = element.get_attribute('outerHTML')
            soup = BeautifulSoup(html_current, 'html.parser')

            # 取得した行内のtd要素をすべて取得
            td_elements = soup.find_all('td')

            # 4つずつグループ化してテキストに追加
            for i in range(0, len(td_elements), 4):
                group = td_elements[i:i + 4]
                if len(group) == 4:  # 4つの要素が揃った場合のみ処理

                    # 月が変わっていればループを終了
                    if day_date.month != current_month:
                        break

                    # 曜日の判定とフォーマット設定
                    if jpholiday.is_holiday(day_date):
                        weekday_jp = "祝"
                    else:
                        weekday_str = day_date.strftime("%A")
                        weekday_jp = {
                            "Monday": "月",
                            "Tuesday": "火",
                            "Wednesday": "水",
                            "Thursday": "木",
                            "Friday": "金",
                            "Saturday": "土",
                            "Sunday": "日"
                        }[weekday_str]

                    # 各時間帯と予約状況をリストに追加（〇で土日祝の場合のみ）
                    for idx, td in enumerate(group):
                        time_slot = time_slots[idx]
                        status = td.get_text(strip=True)
                        if status == "〇" and (weekday_jp in ["土", "日", "祝"]):
                            # 日付、曜日、場所情報をリストに追加
                            availability_list.append((day_date, f"{day_date.strftime('%Y/%m/%d')}({weekday_jp}) ({location}) ({time_slot})<br>"))

                    # 次の日付に進める
                    day_date += timedelta(days=1)

        # 次の月のボタンが存在するかチェック
        try:
            next_month_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[3]/div[5]/div/div[3]"))
            )
            # イメージタグが含まれているか確認
            if next_month_button.find_element(By.TAG_NAME, "img"):
                next_month_button.click()  # 翌月へ進む
                # 明示的に current_date を翌月の1日にリセット
                current_date = (current_date + timedelta(days=31)).replace(day=1)
            else:
                break  # イメージタグがなければループ終了
        except:
            # ボタンが存在しない場合、ループを終了
            break

    # WebDriverを終了
    driver.quit()
    
    # 日付順にソート
    availability_list.sort(key=lambda x: x[0])

    # ソート後の結果を `results` に追加
    for item in availability_list:
        results.append(item[1])

    return results

# マルチスレッドでURLを処理し、結果をコンソールに出力
with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
    futures = {executor.submit(process_url, area, url_info): area for area, url_info in urls.items()}
    for future in futures:
        result = future.result()
        # コンソールに出力
        for line in result:
            print(line)
