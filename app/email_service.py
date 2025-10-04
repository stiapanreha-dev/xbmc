"""
Сервис для отправки email через SMTP
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'localhost')
        self.smtp_port = int(os.getenv('SMTP_PORT', '1025'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@xbmc.local')
        self.from_name = os.getenv('FROM_NAME', 'XBMC')

    def send_email(self, to_email, subject, html_content):
        """Отправка email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'{self.from_name} <{self.from_email}>'
            msg['To'] = to_email

            # HTML часть
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Подключаемся к SMTP серверу с SSL/TLS
            if self.smtp_port == 465:
                # SSL (порт 465)
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # STARTTLS (порт 587) или без шифрования (порт 25/1025)
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    if self.smtp_port == 587:
                        server.starttls()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            return True

        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            return False

    def send_verification_code(self, to_email, code):
        """Отправка кода верификации"""
        subject = 'Подтверждение email - XBMC'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #007bff;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    background-color: #f8f9fa;
                    padding: 30px;
                    margin: 20px 0;
                }}
                .code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #007bff;
                    text-align: center;
                    padding: 20px;
                    background-color: white;
                    border: 2px dashed #007bff;
                    letter-spacing: 5px;
                }}
                .footer {{
                    text-align: center;
                    color: #6c757d;
                    font-size: 12px;
                    padding: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>XBMC - Подтверждение Email</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте!</p>
                    <p>Для завершения регистрации на платформе XBMC введите этот код подтверждения:</p>
                    <div class="code">{code}</div>
                    <p><strong>Код действителен в течение 10 минут.</strong></p>
                    <p>Если вы не регистрировались на XBMC, просто проигнорируйте это письмо.</p>
                </div>
                <div class="footer">
                    <p>С уважением,<br>Команда XBMC</p>
                    <p>Это автоматическое письмо, не отвечайте на него.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_content)

    @staticmethod
    def generate_verification_code(length=6):
        """Генерация числового кода верификации"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


# Singleton instance
email_service = EmailService()
