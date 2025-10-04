#!/usr/bin/env python3
"""
Тест SMTP с проверкой IP адреса
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

def check_external_ip():
    """Проверка внешнего IP"""
    import requests
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
        print(f"Ваш текущий внешний IP: {ip}")
        return ip
    except:
        print("Не удалось определить внешний IP")
        return None

def test_smtp_connection():
    """Тест подключения к SMTP"""
    import smtplib

    smtp_host = os.getenv('SMTP_HOST', 'smtp.timeweb.ru')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))

    print(f"\nПопытка подключения к {smtp_host}:{smtp_port}...")

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            if smtp_port == 587:
                server.starttls()

        print("✓ Успешное подключение к SMTP!")

        # Пробуем авторизацию
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
            print("✓ Успешная авторизация!")

        server.quit()
        return True

    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        return False

def test_send_email():
    """Отправка тестового письма"""
    from app.email_service import email_service

    email = input("\nВведите email для теста (или Enter для пропуска): ").strip()
    if not email:
        print("Отправка письма пропущена")
        return

    print(f"\nОтправка тестового письма на {email}...")
    result = email_service.send_verification_code(email, "123456")

    if result:
        print("✓ Письмо отправлено успешно!")
    else:
        print("✗ Ошибка отправки письма")

if __name__ == '__main__':
    print("=" * 50)
    print("Тест SMTP подключения")
    print("=" * 50)

    # Проверяем IP
    current_ip = check_external_ip()

    if current_ip == "167.172.182.194":
        print("\n⚠️  ВНИМАНИЕ: Вы используете VPN (DigitalOcean IP)")
        print("Для корректной работы SMTP отключите VPN или")
        print("добавьте исключение для smtp.timeweb.ru")
        print("\nЖелаемый IP: 178.124.206.31")
        proceed = input("\nПродолжить тестирование? (y/n): ").strip().lower()
        if proceed != 'y':
            sys.exit(0)

    # Тестируем SMTP
    if test_smtp_connection():
        test_send_email()
