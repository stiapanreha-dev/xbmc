#!/usr/bin/env python3
"""
Тесты для email сервиса
"""
import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

def test_email_configuration():
    """Проверка конфигурации email сервиса"""
    from app.email_service import email_service

    assert email_service.smtp_host, "SMTP_HOST не настроен"
    assert email_service.smtp_port, "SMTP_PORT не настроен"
    print(f"✓ SMTP настроен: {email_service.smtp_host}:{email_service.smtp_port}")

def test_send_verification_email():
    """Тест отправки верификационного email"""
    from app.email_service import email_service

    test_email = input("Введите email для теста (или Enter для пропуска): ").strip()
    if not test_email:
        print("⊘ Тест пропущен")
        return

    test_code = "123456"
    print(f"Отправка кода {test_code} на {test_email}...")

    result = email_service.send_verification_code(test_email, test_code)

    if result:
        print("✓ Email отправлен успешно!")
    else:
        print("✗ Ошибка отправки email")
        raise AssertionError("Не удалось отправить email")

if __name__ == '__main__':
    print("=== Тесты Email Сервиса ===\n")

    try:
        test_email_configuration()
        test_send_verification_email()
        print("\n✓ Все тесты пройдены!")
    except Exception as e:
        print(f"\n✗ Тесты провалены: {e}")
        sys.exit(1)
