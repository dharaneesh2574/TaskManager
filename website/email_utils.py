import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText




def send_email(to_email, subject, body):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587   
    smtp_username = 'vistaes17@gmail.com'
    smtp_password = 'jqelrzqnlpaonqnd'

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
