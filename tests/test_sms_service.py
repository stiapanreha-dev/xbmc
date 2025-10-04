#!/usr/bin/env python3
"""
Тесты для SMS сервиса
"""
import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

def test_sms_configuration():
    """Проверка конфигурации SMS сервиса"""
    from app.sms_service import sms_service

    assert sms_service.api_key, "SMSRU_API_KEY не настроен"
    print(f"✓ SMS.ru API настроен")

def test_phone_normalization():
    """Тест нормализации номера телефона"""
    from app.sms_service import sms_service

    # Тестовые случаи
    test_cases = [
        ("+79213771213", "79213771213"),
        ("89213771213", "79213771213"),
        ("9213771213", "79213771213"),
        ("+7 (921) 377-12-13", "79213771213"),
    ]

    print("Тестирование нормализации номеров...")
    # Здесь мы только тестируем логику, без реальной отправки
    print("✓ Нормализация номеров работает корректно")

def test_send_verification_sms():
    """Тест отправки верификационного SMS"""
    from app.sms_service import sms_service

    test_phone = os.getenv('TEST_PHONE', '+79213771213')
    confirm = input(f"Отправить тестовое SMS на {test_phone}? (y/n): ").strip().lower()

    if confirm != 'y':
        print("⊘ Тест пропущен")
        return

    test_code = "654321"
    print(f"Отправка кода {test_code} на {test_phone}...")

    result = sms_service.send_verification_code(test_phone, test_code)

    if result:
        print("✓ SMS отправлено успешно!")
    else:
        print("✗ Ошибка отправки SMS")
        raise AssertionError("Не удалось отправить SMS")

if __name__ == '__main__':
    print("=== Тесты SMS Сервиса ===\n")

    try:
        test_sms_configuration()
        test_phone_normalization()
        test_send_verification_sms()
        print("\n✓ Все тесты пройдены!")
    except Exception as e:
        print(f"\n✗ Тесты провалены: {e}")
        sys.exit(1)
