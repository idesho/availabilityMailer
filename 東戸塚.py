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
options.add_argument('--headless')
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

        if current_time.day > 11 or (current_time.day == 11 and current_time.hour >= 12):
            subject_month = 3
        else:
            subject_month = 2

        while process_count < subject_month:
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            trs = soup.find_all("tr")[center["trs_range"]]

            current_year_month = (datetime.now() + timedelta(days=30 * process_count)).strftime('%Y/%-m')
            today = datetime.now().timestamp()
            tr_named_array = {}

            for tr_index, tr_element in enumerate(trs):
                td_elements = tr_element.find_all('td')
                for td_index, td_element in enumerate(td_elements):
                    class_attribute = td_element.get('class')
                    if class_attribute == ["text-center", "col_mm_day"] or class_attribute == ["text-center", "col_mm_day", "bd-b"] or class_attribute == ["text-center", "col_mm_day", "bd-r"]:
                        date = td_index + 1
                        key = datetime.strptime(f"{current_year_month}/{date}", "%Y/%m/%d").timestamp()
                        if key >= today:
                            if key not in tr_named_array:
                                tr_named_array[key] = []
                            tr_named_array[key].append(center["names"][tr_index])

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
    driver.quit()  # Close the browser
