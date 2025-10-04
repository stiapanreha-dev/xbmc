# Тесты

Эта папка содержит тесты для проверки функциональности приложения.

## Структура

- `test_email_service.py` - Тесты email сервиса (SMTP)
- `test_sms_service.py` - Тесты SMS сервиса (SMS.ru)

## Запуск тестов

### Тест Email сервиса
```bash
python3 tests/test_email_service.py
```

### Тест SMS сервиса
```bash
python3 tests/test_sms_service.py
```

### Запуск всех тестов
```bash
python3 -m pytest tests/
```

## Добавление новых тестов

При создании новых тестов:
1. Называйте файлы с префиксом `test_`
2. Используйте функции с префиксом `test_`
3. Добавляйте документацию к тестам
4. Обновляйте этот README
