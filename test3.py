# test3.py
# test2.py を改修せずに安定実行するラッパー。
# - URLS をこのファイルにも保持（明示）
# - Selenium の待機/クリックを堅牢化（10s→最低30s、JSクリックにフォールバック）
# - 内部並列を控えめに（MAX_WORKERS を 2 に上書き）
# 使い方: python3 test3.py

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import importlib

# ====== 明示の URL 一覧（test2.py と同一） ======
URLS: dict[str, str] = {
    '白幡': "https://shirahatac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '矢向': "https://yakoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '潮田': "https://ushiodac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '寺尾': "https://teraoc-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '生麦': "https://namamugic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '末吉': "https://sueyoshic-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '長津田': "https://nagatsutac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '中川西': "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '仲町台': "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=02",
    '北山田': "https://tsuzuki-koryu-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=03",
    '中山':   "https://nakayamac-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
    '都筑':   "https://tsuzuki-center-nexres.azurewebsites.net/nexres/KR/KSR0100/index.php?mokuteki=01",
}

# ====== Selenium の待機/クリックをパッチ ======
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait as _OrigWait
from selenium.webdriver.remote.webelement import WebElement as _OrigWebElement
from selenium.common.exceptions import WebDriverException

class _PatchedWait(_OrigWait):
    """10秒指定でも最低30秒は待つ"""
    def __init__(self, driver, timeout=10, poll_frequency=0.5, ignored_exceptions=None):
        super().__init__(driver, timeout=max(timeout, 30),
                         poll_frequency=poll_frequency,
                         ignored_exceptions=ignored_exceptions)

def _patched_click(self, *args, **kwargs):
    """通常クリックが失敗したらJSクリックへフォールバック"""
    try:
        return _OrigWebElement.click(self, *args, **kwargs)
    except WebDriverException:
        drv = getattr(self, "_parent", None)
        if drv is None:
            raise
        try:
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", self)
        except Exception:
            pass
        drv.execute_script("arguments[0].click();", self)

# 実パッチ適用
import selenium.webdriver.support.wait as _wait_mod
_wait_mod.WebDriverWait = _PatchedWait          # type: ignore
_OrigWebElement.click = _patched_click          # type: ignore

# ====== 実行（test2.scrape を利用しつつ上書き注入） ======
def main():
    t2 = importlib.import_module("test2")

    # URLS を上書き（このファイルの定義を使用）
    setattr(t2, "URLS", URLS)

    # 並列を控えめに（CI安定化）
    if hasattr(t2, "MAX_WORKERS"):
        try:
            if int(getattr(t2, "MAX_WORKERS")) > 2:
                setattr(t2, "MAX_WORKERS", 2)
        except Exception:
            setattr(t2, "MAX_WORKERS", 2)
    else:
        setattr(t2, "MAX_WORKERS", 2)

    # そのまま test2.scrape() を実行して標準出力へ
    if hasattr(t2, "scrape"):
        html = t2.scrape()
        print(html)
    else:
        # 念のため main 実行にフォールバック
        import runpy
        runpy.run_module("test2", run_name="__main__")

if __name__ == "__main__":
    main()
