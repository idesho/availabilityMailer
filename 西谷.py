from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import jpholiday
from datetime import datetime, timedelta


# Seleniumのセットアップ
driver = webdriver.Chrome()  # Chrome WebDriverを使用する例です。他のWebDriverを使用する場合は、適切に変更してください。
driver.get("https://yoyaku.hodogaya-kumin.org/reserve/yoyakulist/center/3")

try:
    # 処理回数をカウントする変数
    process_count = 0
    current_time = datetime.now()

    # 条件分岐
    if current_time.day >= 11 and current_time.hour >= 12:
        subject_month = 3
    else:
        subject_month = 2

    print("西谷地区センターの空き状況<br>")
    while process_count < subject_month:
        # すべてのtr要素が読み込まれるまで待機
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))

        # BeautifulSoupを使用してHTMLを解析
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 2番目から13番目のtrタグを取得
        trs = soup.find_all("tr")[1:13]

        # 現在の年月日を取得し、次の月を計算
        current_year_month = (datetime.now() + timedelta(days=30 * process_count)).strftime('%Y/%-m')
        current_date = datetime.now().strftime('%-j')

        # 体育室の施設名リスト
        names = [
            "体育室(A) 9:00-12:00", "体育室(A) 12:00-15:00", "体育室(A) 15:00-18:00", "体育室(A) 18:00-21:00",
            "体育室(B) 9:00-12:00", "体育室(B) 12:00-15:00", "体育室(B) 15:00-18:00", "体育室(B) 18:00-21:00",
            "体育室(C) 9:00-12:00", "体育室(C) 12:00-15:00", "体育室(C) 15:00-18:00", "体育室(C) 18:00-21:00"
        ]

        # データを格納する辞書
        tr_named_array = {}

        # 2番目から13番目のtrタグの要素を処理
        for tr_index, tr_element in enumerate(trs):
            td_elements = tr_element.find_all('td')
            for td_index, td_element in enumerate(td_elements):
                class_attribute = td_element.get('class')
                if class_attribute == ["text-center", "col_mm_day"]:
                    date = td_index + 1
                    key = datetime.strptime(f"{current_year_month}/{date}", "%Y/%m/%d").timestamp()
                    if key >= datetime.now().timestamp():  # 今日以降の日付のみ処理する
                        if key not in tr_named_array:
                            tr_named_array[key] = []
                        tr_named_array[key].append(names[tr_index])

        # 日付順にソート
        sorted_dates = sorted(tr_named_array.keys())

        # 曜日の辞書
        weekdays_japanese = {
            'Mon': '月',
            'Tue': '火',
            'Wed': '水',
            'Thu': '木',
            'Fri': '金',
            'Sat': '土',
            'Sun': '日'
        }

        # ソートされた日付ごとに出力
        for key in sorted_dates:
            formatted_date = datetime.fromtimestamp(key).strftime('%Y/%-m/%-d')
            weekday = datetime.fromtimestamp(key).strftime('%a')
            japanese_weekday = weekdays_japanese[weekday]
            if jpholiday.is_holiday(datetime.fromtimestamp(key)):
                japanese_weekday = "祝"
            for facility in tr_named_array[key]:
                if japanese_weekday in ["土", "日", "祝"]:
                    print(f"{formatted_date}({japanese_weekday}) {facility}<br>")

        # 次のページに遷移するボタンを押す
        next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="contents_wide"]/form/div[1]/button[2]')))
        next_button.click()

        # 処理回数をインクリメント
        process_count += 1

finally:
    driver.quit()  # ブラウザを閉じる
