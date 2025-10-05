# Инструкция по обновлению (исправление кодировки)

## Проблема
Русский текст отображается неправильно (кракозябры вместо кириллицы).

## Решение
1. Добавлен параметр `charset='utf8'` в подключение к MSSQL
2. Добавлены HTTP заголовки с `charset=utf-8`
3. Настройка Apache для передачи правильной кодировки

## Полная инструкция

См. файл **APACHE_CHARSET_FIX.md** - в нем пошаговая инструкция с настройкой Apache.

## Краткая версия для опытных пользователей

### 1. Обновите код через Git

```cmd
cd C:\soft\business.db
git pull origin master
```

### 2. Настройте Apache

Добавьте в `C:\xampp\apache\conf\extra\httpd-vhosts.conf`:

```apache
<VirtualHost *:443>
    ServerName businessdb.ru
    AddDefaultCharset UTF-8  # <-- Добавьте эту строку
    ...
</VirtualHost>
```

### 3. Перезапустите сервисы

```cmd
REM Перезапуск Apache
cd C:\xampp
apache_stop.bat && apache_start.bat

REM Перезапуск Flask
nssm restart FlaskBusinessDB
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
nssm restart FlaskBusinessDB
```

## Проверка

После перезапуска откройте https://businessdb.ru/ и проверьте, что русский текст отображается корректно.

Если проблема сохраняется, проверьте кодировку в самой базе данных MSSQL (должна быть Cyrillic_General_CI_AS или UTF-8).
