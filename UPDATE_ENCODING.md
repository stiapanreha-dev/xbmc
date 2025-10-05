# Инструкция по обновлению (исправление кодировки)

## Проблема
Русский текст отображается неправильно (кракозябры вместо кириллицы).

## Решение
Добавлен параметр `charset='utf8'` в подключение к MSSQL базе данных.

## Как обновить production сервер

### Вариант 1: Автоматическое обновление через Git

```cmd
cd C:\soft\business.db

REM Останавливаем сервис
nssm stop flask_app

REM Обновляем код
git pull origin master

REM Запускаем сервис
nssm start flask_app
```

### Вариант 2: Ручное обновление (если git недоступен)

1. Откройте файл `C:\soft\business.db\app\mssql.py`

2. Найдите функцию `get_connection()` (строка ~13)

3. Добавьте параметр `charset='utf8'` в вызов `pymssql.connect()`:

```python
def get_connection(self):
    try:
        return pymssql.connect(
            server=self.server,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            charset='utf8'  # <-- Добавьте эту строку
        )
```

4. Перезапустите службу:
```cmd
nssm restart flask_app
```

## Проверка

После перезапуска откройте https://businessdb.ru/ и проверьте, что русский текст отображается корректно.

Если проблема сохраняется, проверьте кодировку в самой базе данных MSSQL (должна быть Cyrillic_General_CI_AS или UTF-8).
