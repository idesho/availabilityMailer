import datetime
import jpholiday
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from datetime import timedelta

def get_weekday_jp(date_str):
    date = datetime.datetime.strptime(date_str, "%Y/%m/%d")
    weekday = date.strftime("%A")

    weekdays_jp = {
        "Monday": "月",
        "Tuesday": "火",
        "Wednesday": "水",
        "Thursday": "木",
        "Friday": "金",
        "Saturday": "土",
        "Sunday": "日"
    }

    weekday_jp = weekdays_jp.get(weekday, "")
    holiday_name = jpholiday.is_holiday_name(date)
    if holiday_name:
        weekday_jp = "祝"

    return weekday_jp

def process_element(element, start_date, section):
    div_html = element.get_attribute('outerHTML')
    soup = BeautifulSoup(div_html, 'html.parser')
    second_level_div = soup.find_all(recursive=False)[0]
    second_level_div.unwrap()
    top_level_divs = soup.find_all('div', recursive=False)
    first_bottom_element = top_level_divs[0].text.strip()
    schedule_data = []
    today = datetime.datetime.today().date()

    for i, div in enumerate(top_level_divs[1:], start=1):
        style = div.get('style', '')
        if 'background-color: rgb(255, 255, 255)' in style:
            date = start_date + timedelta(days=i-1)
            date_str = date.strftime("%Y/%m/%d")
            weekday_jp = get_weekday_jp(date_str)
            if date >= today:
                if weekday_jp in ["土", "日", "祝"]:
                    schedule_data.append((date_str, weekday_jp, first_bottom_element, section))

    return schedule_data

def click_next_month_button(driver):
    next_month_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div/div/div/div[1]/div/div[2]/div[2]/div/div/div/div[1]/div/div/div[3]/div[1]/div[3]')
    next_month_button.click()
    time.sleep(4)

def process_center(driver, center, loops):
    driver.get(center["url"])
    print(f"<br>{center['name']}の空き状況<br>")
    time.sleep(4)

    start_date = datetime.datetime.today().replace(day=1).date()
    all_schedule_data = []

    for _ in range(loops):
        for ranges, section in center["sections"]:
            for idx in ranges:
                try:
                    div_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, f'//*[@id="root"]/div/div/div/div/div/div/div[1]/div/div[2]/div[2]/div/div/div/div[1]/div/div/div[3]/div[3]/div/div/div/div[2]/div[{idx}]'))
                    )
                    all_schedule_data.extend(process_element(div_element, start_date, section))
                except Exception as e:
                    print(f"要素が見つかりませんでした: {e}")

        all_schedule_data.sort(key=lambda x: x[0])
        for data in all_schedule_data:
            print(f"{data[0]} ({data[1]}) ({data[2]}:{data[3]})"+ "<br>")

        click_next_month_button(driver)
        all_schedule_data = []
        start_date = (start_date + timedelta(days=32)).replace(day=1)

centers = [
    {
        "name": "神奈川地区センター",
        "url": "https://ufss.f-supportsys2.com/stt?c=r&d=0a0bmv1_v&i=0_0bmv1_v&r=d&a=0",
        "sections": [
            (range(38, 42), '体育室左面'),
            (range(43, 47), '体育室中面'),
            (range(52, 56), '体育室右面')
        ]
    },
    {
        "name": "神大寺地区センター",
        "url": "https://ufss.f-supportsys2.com/stt?c=r&d=0a0bmv1_v&i=a_0bmv1_v&r=d&a=0",
        "sections": [
            (range(38, 42), '体育室手前'),
            (range(43, 47), '体育室中央'),
            (range(52, 56), '体育室奥')
        ]
    },
    {
        "name": "菅田地区センター",
        "url": "https://ufss.f-supportsys2.com/stt?c=r&d=0a0bmv1_v&i=C_0bmv1_v&r=d&a=0",
        "sections": [
            (range(41, 46), '体育室手前'),
            (range(51, 56), '体育室中央'),
            (range(57, 62), '体育室奥')
        ]
    },
    # 他の地区センターの情報をここに追加
]

driver = webdriver.Chrome()

try:
    for center in centers:
        now = datetime.datetime.now()
        loops = 3 if (now.day > 12 or (now.day == 12 and now.hour >= 9)) else 2
        process_center(driver, center, loops)
except Exception as e:
    print("エラーが発生しました:", e)
finally:
    driver.quit()
