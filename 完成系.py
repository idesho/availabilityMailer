from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import jpholiday

# 曜日を日本語で取得する関数
def get_weekday_jp(date_str):
    """指定された日付文字列の曜日を日本語で返し、祝日をチェックする。"""
    date = datetime.strptime(date_str, "%Y/%m/%d")
    weekday = date.strftime("%A")
    weekday_jp_dict = {
        "Monday": "月",
        "Tuesday": "火",
        "Wednesday": "水",
        "Thursday": "木",
        "Friday": "金",
        "Saturday": "土",
        "Sunday": "日"
    }
    weekday_jp = weekday_jp_dict.get(weekday, "")
    holiday_name = jpholiday.is_holiday_name(date)
    if holiday_name:
        weekday_jp = "祝"
    return weekday_jp

# 指定されたURLの空き状況を取得する関数
def check_availability(driver):
    """指定されたURLの空き状況を取得して表示する。"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/form/table[1]/tbody/tr[3]/td/table/tbody/tr/td[4]"))
        )
    except TimeoutException:
        print("ページの読み込みがタイムアウトしました。")
        return None
    
    page_source = driver.page_source
    return page_source

# HTMLソースから空き状況を解析する関数
def parse_availability(page_source, current_year, current_month, id_range):
    """HTMLソースから空き状況を解析して日付情報を取得する。"""
    soup = BeautifulSoup(page_source, 'html.parser')
    date_info = []
    for i in id_range:
        td = soup.find('td', id=f'right_v{i}')
        if td:
            tr = td.find_parent('tr')
            if tr:
                if id_range.start <= i < id_range.start + 4:
                    gym_info = "体育室A"
                elif id_range.start + 4 <= i < id_range.start + 8:
                    gym_info = "体育室B"
                elif id_range.start + 8 <= i < id_range.stop:
                    gym_info = "体育室C"
                else:
                    gym_info = ""
                time_slot = td.text.strip()
                for td in tr.find_all('td'):
                    onmouseover = td.get('onmouseover')
                    if onmouseover:
                        parts = onmouseover.split(',')
                        if len(parts) >= 3:
                            day = int(parts[0].split('(')[-1]) + 1
                            if 1 <= day <= 31:
                                if not (('style' in td.attrs and 'background-color:#333333' in td['style']) or '×' in td.text):
                                    date_str = f"{current_year}/{current_month:02}/{day:02}"
                                    weekday_jp = get_weekday_jp(date_str)
                                    date_info.append((date_str, weekday_jp, time_slot, gym_info))
    
    date_info_sorted = sorted(date_info, key=lambda x: datetime.strptime(x[0], "%Y/%m/%d"))
    return date_info_sorted

# 結果をコンソールに出力する関数
def display_results(date_info_sorted):
    """解析した日付情報をコンソールに出力する。"""
    today = datetime.now()
    for date_str, weekday_jp, time_slot, gym_info in date_info_sorted:
        date = datetime.strptime(date_str, "%Y/%m/%d")
        if date >= today and (weekday_jp in ["土", "日", "祝"]):
            print(f"{date_str} ({weekday_jp}) ({time_slot}: {gym_info})<br>")

# メイン処理
if __name__ == "__main__":
    centers = [
        {"url": "https://yokohama-shisetsu.com/yoyaku_test/wb_pub.php?sisetu_code=02", "range": range(8, 20), "name": "藤が丘地区センター"},
        {"url": "https://yokohama-shisetsu.com/yoyaku_test/wb_pub.php?sisetu_code=03", "range": range(0, 12), "name": "若草台地区センター"},
        {"url": "https://yokohama-shisetsu.com/yoyaku_test/wb_pub.php?sisetu_code=04", "range": range(0, 12), "name": "美しが丘西地区センター"},
        {"url": "https://yokohama-shisetsu.com/yoyaku_test/wb_pub.php?sisetu_code=05", "range": range(0, 12), "name": "奈良地区センター"},
    ]
    
    # Chromeのオプションを設定
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')  # 必要に応じて追加
    options.add_argument('--window-size=1920x1080')  # 必要に応じて追加

    driver = webdriver.Chrome(options=options)
    
    for center in centers:
        print(f"<br>{center['name']}の空き状況"+"<br>")
        url = center["url"]
        id_range = center["range"]
        
        driver.get(url)
        
        current_year = datetime.now().year
        current_month = datetime.now().month

        while True:
            page_source = check_availability(driver)
            if page_source:
                date_info_sorted = parse_availability(page_source, current_year, current_month, id_range)
                display_results(date_info_sorted)
            
            try:
                next_button = driver.find_element(By.XPATH, "/html/body/form/table[1]/tbody/tr[3]/td/table/tbody/tr/td[4]/span")
                next_button.click()
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
            except (TimeoutException, NoSuchElementException):
                break
    
    driver.quit()
