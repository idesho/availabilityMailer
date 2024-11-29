import time
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import concurrent.futures
import subprocess
from pytz import timezone

# 処理開始時間を記録
start_time = time.time()
load_dotenv()

def run_command(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout

commands = [
    "python3 test.py",
    "python3 小綱篠.py",
    "python3 西谷.py",
    "python3 神奈川.py",
    "python3 完成系.py",
    "python3 試作.py"
]

# 並行してコマンドを実行
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(run_command, commands))

# 結果を結合
result = "".join(results)

# 送信先のメールアドレスを取得
to_emails = os.getenv('TO_EMAILS').split(',')

# 現在時刻を日本時間に変換
now_utc = datetime.now(timezone('UTC'))  # UTCの現在時刻を取得
now_jst = now_utc.astimezone(timezone('Asia/Tokyo'))  # JSTに変換
subject = f"{now_jst.strftime('%Y/%m/%d %H時%M分')}現在の空き状況"

# メールの作成
msg = MIMEMultipart()
msg['From'] = os.getenv('SMTP_USERNAME')
msg['To'] = ', '.join(to_emails)
msg['Subject'] = subject
msg.attach(MIMEText(result, 'html'))

# メールの送信
try:
    server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')))
    server.starttls()
    server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
    server.sendmail(os.getenv('SMTP_USERNAME'), to_emails, msg.as_string())
    server.quit()
    print('送信完了')
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"処理時間: {elapsed_time:.2f}秒")
except Exception as e:
    print(f"Message could not be sent. Error: {e}")
