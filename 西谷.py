from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import jpholiday
from datetime import datetime, timedelta
from selenium.webdriver.chrome.options import Options

def get_weekday_jp(date):
    weekday = date.strftime("%a")
    weekdays_japanese = {
        'Mon': '月',
        'Tue': '火',
        'Wed': '水',
        'Thu': '木',
        'Fri': '金',
        'Sat': '土',
        'Sun': '日'
    }
    japanese_weekday = weekdays_japanese[weekday]
    if jpholiday.is_holiday(date):
        japanese_weekday = "祝"
    return japanese_weekday

# Chromeのオプションを設定
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920x1080')

# Seleniumのセットアップ
driver = webdriver.Chrome(options=options)  # ヘッドレスモードで起動
driver.get("https://yoyaku.hodogaya-kumin.org/reserve/yoyakulist/center/3")

try:
    process_count = 0
    current_time = datetime.now()

    if current_time.day >= 11 and current_time.hour >= 12:
        subject_month = 3
    else:
        subject_month = 2

    print("西谷地区センターの空き状況<br>")
    while process_count < subject_month:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))

        soup = BeautifulSoup(driver.page_source, "html.parser")

        trs = soup.find_all("tr")[1:13]

        current_year_month = (datetime.now() + timedelta(days=30 * process_count)).strftime('%Y/%-m')
        today = datetime.now().timestamp()

        names = [
            "体育室(A) 9:00-12:00", "体育室(A) 12:00-15:00", "体育室(A) 15:00-18:00", "体育室(A) 18:00-21:00",
            "体育室(B) 9:00-12:00", "体育室(B) 12:00-15:00", "体育室(B) 15:00-18:00", "体育室(B) 18:00-21:00",
            "体育室(C) 9:00-12:00", "体育室(C) 12:00-15:00", "体育室(C) 15:00-18:00", "体育室(C) 18:00-21:00"
        ]

        tr_named_array = {}

        for tr_index, tr_element in enumerate(trs):
            td_elements = tr_element.find_all('td')
            for td_index, td_element in enumerate(td_elements):
                class_attribute = td_element.get('class')
                if class_attribute == ["text-center", "col_mm_day"]:
                    date = td_index + 1
                    key = datetime.strptime(f"{current_year_month}/{date}", "%Y/%m/%d").timestamp()
                    if key >= today:
                        if key not in tr_named_array:
                            tr_named_array[key] = []
                        tr_named_array[key].append(names[tr_index])

        sorted_dates = sorted(tr_named_array.keys())

        for key in sorted_dates:
            date = datetime.fromtimestamp(key)
            formatted_date = date.strftime('%Y/%-m/%-d')
            japanese_weekday = get_weekday_jp(date)
            for facility in tr_named_array[key]:
                if japanese_weekday in ["土", "日", "祝"]:
                    print(f"{formatted_date}({japanese_weekday}) {facility}<br>")

        next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="contents_wide"]/form/div[1]/button[2]')))
        next_button.click()

        process_count += 1

finally:
    driver.quit()  # ブラウザを閉じる
