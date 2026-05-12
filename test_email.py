import smtplib
from email.mime.text import MIMEText

email_user = "markusmorus2@gmail.com"
email_pass = "vnlwsxzfrpomtyvo"

msg = MIMEText("Test da ReviewPulse")
msg['Subject'] = "Prova invio"
msg['From'] = email_user
msg['To'] = email_user   # invio a te stesso

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(email_user, email_pass)
        server.sendmail(email_user, email_user, msg.as_string())
    print("✅ Email inviata con successo!")
except Exception as e:
    print(f"❌ Errore: {e}")