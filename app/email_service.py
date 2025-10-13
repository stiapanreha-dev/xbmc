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
        self.from_name = os.getenv('FROM_NAME', 'Business database')

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
        subject = 'Подтверждение email - Business database'

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
                    <h1>Business database - Подтверждение Email</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте!</p>
                    <p>Для завершения регистрации на платформе Business database введите этот код подтверждения:</p>
                    <div class="code">{code}</div>
                    <p><strong>Код действителен в течение 10 минут.</strong></p>
                    <p>Если вы не регистрировались на Business database, просто проигнорируйте это письмо.</p>
                </div>
                <div class="footer">
                    <p>С уважением,<br>Команда Business database</p>
                    <p>Это автоматическое письмо, не отвечайте на него.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_content)

    def send_password_email(self, to_email, username, password):
        """Отправка пароля после регистрации"""
        subject = 'Спасибо за регистрацию - Business database'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #212529;
                    margin: 0;
                    padding: 0;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background-color: #0d6efd;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .logo {{
                    max-width: 200px;
                    height: auto;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 24px;
                    font-weight: 600;
                    color: #212529;
                    margin-bottom: 20px;
                }}
                .message {{
                    font-size: 16px;
                    color: #495057;
                    margin-bottom: 30px;
                }}
                .credentials {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #0d6efd;
                    padding: 20px;
                    margin: 30px 0;
                }}
                .credentials-label {{
                    font-size: 14px;
                    color: #6c757d;
                    margin-bottom: 5px;
                }}
                .credentials-value {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #0d6efd;
                    font-family: 'Courier New', monospace;
                    word-break: break-all;
                }}
                .footer {{
                    text-align: center;
                    padding: 30px;
                    background-color: #f8f9fa;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #0d6efd;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: 500;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="https://businessdb.ru/static/images/logo.png" alt="Business database" class="logo">
                </div>
                <div class="content">
                    <div class="greeting">Спасибо за регистрацию!</div>
                    <div class="message">
                        Здравствуйте, <strong>{username}</strong>!<br>
                        Ваш аккаунт в Business database успешно создан.
                    </div>
                    <div class="credentials">
                        <div class="credentials-label">Ваш логин:</div>
                        <div class="credentials-value">{username}</div>
                    </div>
                    <div class="credentials">
                        <div class="credentials-label">Ваш пароль:</div>
                        <div class="credentials-value">{password}</div>
                    </div>
                    <div class="message">
                        Используйте эти данные для входа в систему.<br>
                        Рекомендуем изменить пароль после первого входа в настройках профиля.
                    </div>
                    <center>
                        <a href="https://businessdb.ru/auth/login" class="btn">Войти в систему</a>
                    </center>
                </div>
                <div class="footer">
                    <p>С уважением,<br>Команда Business database</p>
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

    @staticmethod
    def generate_password(length=12):
        """Генерация сильного пароля"""
        import string
        # Используем буквы, цифры и специальные символы
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        # Гарантируем наличие разных типов символов
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice('!@#$%^&*')
        ]
        # Добавляем остальные случайные символы
        for _ in range(length - 4):
            password.append(secrets.choice(chars))
        # Перемешиваем
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)


# Singleton instance
email_service = EmailService()
