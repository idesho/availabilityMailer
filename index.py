import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

# コマンドを実行して結果を取得
output1 = os.popen("python3 test.py").read()
output2 = os.popen("python3 小綱篠.py").read()
output3 = os.popen("python3 西谷.py").read()
output4 = os.popen("python3 神奈川.py").read()
output5 = os.popen("python3 完成系.py").read()
result = f"{output1}{output2}<br>{output3}{output4}{output5}"
# print(result)

# 送信先のメールアドレスを取得
to_emails = os.getenv('TO_EMAILS').split(',')

now = datetime.now()
subject = f"{now.strftime('%Y/%m/%d %H時%M分')}現在の空き状況"

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
except Exception as e:
    print(f"Message could not be sent. Error: {e}")
