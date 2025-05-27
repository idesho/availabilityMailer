from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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

# Chrome options setup
options = Options()
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920x1080')

# URLs and configurations for each center
centers = [
    {
        "name": "東戸塚地区センター",
        "url": "https://uketsuke.chiiki-support.com/reserve/yoyakulist",
        "trs_range": slice(27, 39),
        "names": [
            "体育室(手前) 9:00-12:00", "体育室(手前) 12:00-15:00", "体育室(手前) 15:00-18:00", "体育室(手前) 18:00-21:00",
            "体育室(中央) 9:00-12:00", "体育室(中央) 12:00-15:00", "体育室(中央) 15:00-18:00", "体育室(中央) 18:00-21:00",
            "体育室(奥) 9:00-12:00", "体育室(奥) 12:00-15:00", "体育室(奥) 15:00-18:00", "体育室(奥) 18:00-21:00"
        ]
    }
]

# Selenium setup
driver = webdriver.Chrome(options=options)

try:
    for center in centers:
        print(f"<br>{center['name']}の空き状況<br>")
        driver.get(center["url"])

        # セレクトボックスで「東戸塚地区センター」を選択
        select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "cboCenter"))
        )
        dropdown = Select(select)
        dropdown.select_by_visible_text("東戸塚地区センター")  # セレクトボックスのテキストで選択

        process_count = 0
        current_time = datetime.now()

        # 抽選対象月数の判定
        if current_time.day > 11 or (current_time.day == 11 and current_time.hour >= 12):
            subject_month = 3   # 当月含め3か月先まで
        else:
            subject_month = 2   # 当月含め2か月先まで

        # 基準月（当月1日）を計算
        base_month_first = current_time.replace(day=1)

        while process_count < subject_month:
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            trs = soup.find_all("tr")[center["trs_range"]]

            # ---- 修正ポイント：月をきちんと進める ----
            year  = base_month_first.year  + (base_month_first.month - 1 + process_count) // 12
            month = (base_month_first.month - 1 + process_count) % 12 + 1
            current_year_month = f"{year}/{month:02d}"   # 例: '2025/07'
            # --------------------------------------------

            today_ts = datetime.now().timestamp()
            tr_named_dict = {}

            for tr_index, tr_element in enumerate(trs):
                td_elements = tr_element.find_all('td')
                for td_index, td_element in enumerate(td_elements):
                    class_attribute = td_element.get('class')
                    if class_attribute in [
                        ["text-center", "col_mm_day"],
                        ["text-center", "col_mm_day", "bd-b"],
                        ["text-center", "col_mm_day", "bd-r"]
                    ]:
                        day = td_index + 1
                        key_date = datetime.strptime(f"{current_year_month}/{day}", "%Y/%m/%d")
                        key_ts = key_date.timestamp()
                        if key_ts >= today_ts:
                            tr_named_dict.setdefault(key_ts, []).append(center["names"][tr_index])

            for key_ts in sorted(tr_named_dict.keys()):
                date_obj = datetime.fromtimestamp(key_ts)
                formatted_date = date_obj.strftime('%Y/%-m/%-d')
                jp_weekday = get_weekday_jp(date_obj)
                for facility in tr_named_dict[key_ts]:
                    if jp_weekday in ["土", "日", "祝"]:
                        print(f"{formatted_date}({jp_weekday}) {facility}<br>")

            # 次月へ
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="contents_wide"]/form/div[1]/button[2]')
                )
            )
            next_button.click()
            process_count += 1

finally:
    driver.quit()  # Close the browser
