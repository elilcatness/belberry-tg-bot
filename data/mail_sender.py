from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL, SMTPException

from data.utils import get_config


def send_mail(email, subject, text):
    cfg = get_config()
    try:
        addr_from = cfg['smtp_from']
        password = cfg['smtp_password']

        msg = MIMEMultipart()
        msg['From'] = addr_from
        msg['To'] = email
        msg['Subject'] = subject

        body = text
        msg.attach(MIMEText(body, 'html'))

        server = SMTP_SSL(cfg['smtp_host'], cfg['smtp_port'])
        server.login(addr_from, password)

        server.send_message(msg)
        server.quit()
        return True
    except SMTPException:
        return False
