'''



푸시 알림 기능.
이메일, 텔레그램, 디스코드 등 이용하여 작업 오류,결과, 진행 상황 알림 전송
'''

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def email_alert(message, to_email):
    sender_email = 'your_email@gmail.com'
    sender_password = 'your_password'
    subject = 'Alert from Python Script'
    body = message

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")


def push_alert(message, platform='email'):
    if platform == 'email':
        pass
    elif platform == 'telegram':
        pass
    elif platform == 'discord':
        pass


