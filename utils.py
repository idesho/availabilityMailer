from datetime import date, datetime

import jpholiday


JP_WEEKDAY = {
    "Monday": "月",
    "Tuesday": "火",
    "Wednesday": "水",
    "Thursday": "木",
    "Friday": "金",
    "Saturday": "土",
    "Sunday": "日",
}


def _to_datetime(date_input):
    if isinstance(date_input, datetime):
        return date_input
    if isinstance(date_input, date):
        return datetime.combine(date_input, datetime.min.time())
    if isinstance(date_input, str):
        return datetime.strptime(date_input, "%Y/%m/%d")
    raise TypeError("date_input must be datetime, date, or 'YYYY/MM/DD' string")


def get_weekday_jp(date_input) -> str:
    dt = _to_datetime(date_input)
    if jpholiday.is_holiday(dt):
        return "祝"
    return JP_WEEKDAY.get(dt.strftime("%A"), "")


def is_weekend_or_holiday(date_input) -> bool:
    return get_weekday_jp(date_input) in ("土", "日", "祝")
