# import time
# import os
# from datetime import datetime
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from dotenv import load_dotenv
# import concurrent.futures
# import subprocess
# from pytz import timezone

# # 処理開始時間を記録
# start_time = time.time()
# load_dotenv()

# def run_command(command):
#     return subprocess.run(command, shell=True, capture_output=True, text=True).stdout

# commands = [
#     "python3 test2.py",
#     "python3 小綱篠.py",
#     "python3 西谷.py",
#     "python3 神奈川.py",
#     "python3 完成系.py",
#     "python3 試作.py",
#     "python3 東戸塚.py"
# ]

# # 並行してコマンドを実行
# with concurrent.futures.ThreadPoolExecutor() as executor:
#     results = list(executor.map(run_command, commands))

# # 結果を結合
# result = "".join(results)

# # 送信先のメールアドレスを取得
# to_emails = os.getenv('TO_EMAILS').split(',')

# # 現在時刻を日本時間に変換
# now_utc = datetime.now(timezone('UTC'))  # UTCの現在時刻を取得
# now_jst = now_utc.astimezone(timezone('Asia/Tokyo'))  # JSTに変換
# subject = f"{now_jst.strftime('%Y/%m/%d %H時%M分')}現在の空き状況"

# # メールの作成
# msg = MIMEMultipart()
# msg['From'] = os.getenv('SMTP_USERNAME')
# msg['To'] = ', '.join(to_emails)
# msg['Subject'] = subject
# msg.attach(MIMEText(result, 'html'))

# # メールの送信
# try:
#     server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')))
#     server.starttls()
#     server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
#     server.sendmail(os.getenv('SMTP_USERNAME'), to_emails, msg.as_string())
#     server.quit()
#     print('送信完了')
#     end_time = time.time()
#     elapsed_time = end_time - start_time
#     print(f"処理時間: {elapsed_time:.2f}秒")
# except Exception as e:
#     print(f"Message could not be sent. Error: {e}")

import os
import sys
import html
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import concurrent.futures
import subprocess
from pytz import timezone  # 必要なため、Actionsで pytz をインストール

load_dotenv()
ART = Path("artifacts"); ART.mkdir(exist_ok=True)

# ---- 実行するスクリプト群（shell を使わず配列で安全に呼ぶ） ----
COMMANDS = [
    ["python3", "test2.py"],
    ["python3", "小綱篠.py"],
    ["python3", "西谷.py"],
    ["python3", "神奈川.py"],
    ["python3", "完成系.py"],
    ["python3", "試作.py"],
    ["python3", "東戸塚.py"],
]

def run_command(cmd, timeout=180):
    """サブプロセスを実行し、stdout/stderr/returncode を返す。"""
    name = " ".join(cmd)
    try:
      r = subprocess.run(
          cmd,
          capture_output=True,
          text=True,
          timeout=timeout,
          check=False,      # 失敗しても落とさず本文に載せる
      )
      return {
          "name": name,
          "returncode": r.returncode,
          "stdout": r.stdout or "",
          "stderr": r.stderr or "",
      }
    except subprocess.TimeoutExpired as e:
      return {
          "name": name,
          "returncode": 124,
          "stdout": e.stdout or "",
          "stderr": f"[TIMEOUT] {str(e)}",
      }
    except Exception as e:
      return {
          "name": name,
          "returncode": 1,
          "stdout": "",
          "stderr": f"[EXCEPTION] {repr(e)}",
      }

# 並行実行（過負荷やブロックを避けるなら max_workers を 2〜3 に調整）
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    results = list(ex.map(run_command, COMMANDS))

# 個別ログを artifacts に保存
for res in results:
    safe = res["name"].replace(" ", "_")
    (ART / f"{safe}.out.txt").write_text(res["stdout"], encoding="utf-8")
    (ART / f"{safe}.err.txt").write_text(res["stderr"], encoding="utf-8")

# HTML本文を組み立て（成功/失敗が一目で分かる）
def section_html(res):
    status = "✅ SUCCESS" if res["returncode"] == 0 else f"❌ FAIL (rc={res['returncode']})"
    return f"""
    <details style="margin-bottom:12px;" open>
      <summary><b>{html.escape(res["name"])}</b> — {status}</summary>
      <div>
        <h4>STDOUT</h4>
        <pre style="white-space:pre-wrap; background:#f6f8fa; padding:8px; border-radius:6px;">{html.escape(res["stdout"])}</pre>
        <h4>STDERR</h4>
        <pre style="white-space:pre-wrap; background:#fff5f5; padding:8px; border-radius:6px; border:1px solid #f0c2c2;">{html.escape(res["stderr"])}</pre>
      </div>
    </details>
    """

body_sections = "\n".join(section_html(r) for r in results)
now_utc = datetime.now(timezone('UTC'))
now_jst = now_utc.astimezone(timezone('Asia/Tokyo'))
subject = f"{now_jst.strftime('%Y/%m/%d %H時%M分')}現在の空き状況"

html_body = f"""<!doctype html>
<html lang="ja">
<meta charset="utf-8">
<body style="font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;">
  <h2>{html.escape(subject)}</h2>
  <p>実行ホスト: GitHub Actions（JST） / 生成: {now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
  {body_sections}
</body></html>
"""

# メール送信
to_emails = [e.strip() for e in (os.getenv('TO_EMAILS') or "").split(',') if e.strip()]
if not to_emails:
    (ART / "fatal_no_to_emails.txt").write_text("TO_EMAILS が未設定です。", encoding="utf-8")
    print("TO_EMAILS が未設定です。", file=sys.stderr)
    sys.exit(1)

# 本文も artifacts に保存しておく
(ART / "combined_result.html").write_text(html_body, encoding="utf-8")

msg = MIMEMultipart()
msg['From'] = os.getenv('SMTP_USERNAME')
msg['To'] = ', '.join(to_emails)
msg['Subject'] = subject
msg.attach(MIMEText(html_body, 'html', 'utf-8'))

try:
    server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')))
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
    server.sendmail(os.getenv('SMTP_USERNAME'), to_emails, msg.as_string())
    server.quit()
    print('送信完了')
except Exception as e:
    (ART / "smtp_error.txt").write_text(repr(e), encoding="utf-8")
    print(f"Message could not be sent. Error: {e}", file=sys.stderr)
    sys.exit(1)
