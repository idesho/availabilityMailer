from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import parse_qs
import jpholiday
from datetime import datetime, date
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

# 日付から曜日を取得し、祝日の場合は"(祝)"を追加する関数
def get_weekday(date_str):
    date = datetime.strptime(date_str, "%Y/%m/%d")
    weekday = date.strftime("%A")  # 英語表記の曜日を取得
    
    # 曜日を日本語表記に変換
    if weekday == "Monday":
        weekday_jp = "月"
    elif weekday == "Tuesday":
        weekday_jp = "火"
    elif weekday == "Wednesday":
        weekday_jp = "水"
    elif weekday == "Thursday":
        weekday_jp = "木"
    elif weekday == "Friday":
        weekday_jp = "金"
    elif weekday == "Saturday":
        weekday_jp = "土"
    elif weekday == "Sunday":
        weekday_jp = "日"
    
    # 祝日の判定
    holiday_name = jpholiday.is_holiday_name(date)
    if holiday_name:
        weekday_jp = "祝"
    
    return weekday_jp

# 同じ処理を関数にまとめる
def extract_data_from_td(target_tr, time_td, center, i):
    output = []
    target_tds_without_x = [td for td in target_tr.find_all('td') if '×' not in td.text and ('style' not in td.attrs or 'background-color:#333333' not in td['style'])]
    for td in target_tds_without_x:
        if 'onmouseover' in td.attrs:
            href = td.a['href']
            parsed_href = parse_qs(href)
            year = parsed_href['nen'][0]
            month = parsed_href['tuki'][0]
            day = parsed_href['hi'][0]
            date_str = f"{year}/{month}/{day}"
            weekday = get_weekday(date_str)  # get_weekday 関数を呼び出す
            time = time_td.text.strip()
            gym_info = ""  # 追加情報の初期値を設定

            # 城郷小机地区センターの場合のみ追加情報を含める
            if center["name"] == "城郷小机地区センター":
                if 8 <= i <= 11:
                    gym_info = " (体育室A)"
                elif 12 <= i <= 15:
                    gym_info = " (体育室B)"
                elif 16 <= i <= 19:
                    gym_info = " (体育室C)"
            output.append(f"{date_str} ({weekday}){gym_info} ({time})")
    return output

# Chromeのオプションを設定
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')  # 必要に応じて追加
options.add_argument('--window-size=1920x1080')  # 必要に応じて追加

# ウェブドライバーを起動
driver = webdriver.Chrome(options=options)

# 地区センターごとのURLと範囲を定義
centers = [
    {"url": "https://f-supportsys.com/kouhoku/yoyaku/wb_pub.php?sisetu_code=05", "range": range(16, 20), "name": "篠原地区センター"},
    {"url": "https://f-supportsys.com/kouhoku/yoyaku/wb_pub.php?sisetu_code=03", "range": range(8, 12), "name": "綱島地区センター"},
    {"url": "https://f-supportsys.com/kouhoku/yoyaku/wb_pub.php?sisetu_code=06", "range": range(8, 20), "name": "城郷小机地区センター"}
]

# 出力データを地区センターごとに格納するための辞書
output_data = {center["name"]: [] for center in centers}

for center in centers:
    try:
        # ウェブページにアクセス
        driver.get(center["url"])

        # 処理のループ回数を決定
        today = datetime.today()
        loops = 3 if (today.day == 14 and today.hour >= 10) or (today.day > 14) else 2

        for _ in range(loops):
            # BeautifulSoupでHTMLを解析
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 指定された範囲内のデータを抽出し、整形
            for i in center["range"]:
                target_td = soup.find('td', id=f'right_v{i}')
                if target_td is None:
                    # エラーメッセージを出力して次の地区センターの処理に移る
                    print(f"Error: Could not find element with id 'right_v{i}'")
                    raise ValueError("Element not found")
                
                target_tr = target_td.find_parent('tr')
                time_td = target_td
                output_data[center["name"]].extend(extract_data_from_td(target_tr, time_td, center, i))

            try:
                # 翌月ボタンがクリック可能になるまで待機
                next_month_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='form1']/table[1]/tbody/tr[3]/td/table/tbody/tr/td[3]/span"))
                )
            except TimeoutException:
                # 翌月ボタンが存在しない場合、処理を終了
                break
            
            # 次の月の情報を取得するために、翌月ボタンをクリック
            next_month_button.click()
    except Exception as e:
        print(f"Error occurred during processing {center['name']}: {str(e)}")
        continue

# ソートされた結果を出力
for center_name, data in output_data.items():
    print(f"<br>{center_name}の空き状況<br>")
    sorted_data = sorted(data, key=lambda x: datetime.strptime(x.split()[0], "%Y/%m/%d"))
    today = date.today()
    for item in sorted_data:
        date_str = item.split()[0]
        item_date = datetime.strptime(date_str, "%Y/%m/%d").date()
        if item_date >= today:
            weekday = item.split()[1]  # データから曜日の部分を取得
            if weekday in ["(土)", "(日)", "(祝)"]:  # 曜日が土曜日、日曜日、または祝日であるかどうかをチェック
                print(item + "<br>")

# ブラウザを閉じる
driver.quit()
