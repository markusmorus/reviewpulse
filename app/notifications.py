from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from config import Config

def send_whatsapp(to_number, body):
    client = Client(Config.TWILIO_SID, Config.TWILIO_TOKEN)
    message = client.messages.create(
         body=body,
         from_=Config.TWILIO_WHATSAPP,
         to=f'whatsapp:{to_number}'
    )
    return message.sid

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = Config.EMAIL_USER
    msg['To'] = to_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
        server.sendmail(Config.EMAIL_USER, to_email, msg.as_string())