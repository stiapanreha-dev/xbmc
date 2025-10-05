# Исправление кодировки в Apache + Flask

## Важно! Изменение кодировки MSSQL

База данных хранит данные в кодировке Windows-1251 (cp1251), поэтому изменен параметр подключения.

## Шаг 1: Обновите код через Git

```powershell
cd C:\soft\business.db

# Если git не установлен, используйте: winget install --id Git.Git -e
git pull origin master
```

## Шаг 1.1: Проверьте .env файл (опционально)

Если нужно изменить кодировку, добавьте в `.env`:

```bash
# По умолчанию используется cp1251 (Windows-1251)
MSSQL_CHARSET=cp1251

# Если база в UTF-8, используйте:
# MSSQL_CHARSET=utf8
```

## Шаг 2: Настройте Apache для UTF-8

Откройте файл `C:\xampp\apache\conf\extra\httpd-vhosts.conf` и найдите секцию для businessdb.ru:

```apache
<VirtualHost *:443>
    ServerName businessdb.ru
    ServerAlias www.businessdb.ru

    # Добавьте эту строку для правильной кодировки
    AddDefaultCharset UTF-8

    SSLEngine on
    SSLCertificateFile "C:/xampp/apache/conf/ssl.crt/businessdb.ru.crt"
    SSLCertificateKeyFile "C:/xampp/apache/conf/ssl.key/businessdb.ru.key"

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    ErrorLog "logs/businessdb-error.log"
    CustomLog "logs/businessdb-access.log" common
</VirtualHost>
```

## Шаг 3: Перезапустите сервисы

```powershell
# Перезапуск Apache
cd C:\xampp
.\apache_stop.bat
.\apache_start.bat

# Перезапуск Flask
C:\nssm\win64\nssm.exe restart FlaskBusinessDB
```

## Шаг 4: Очистите кэш браузера

1. Нажмите `Ctrl+Shift+Delete` в браузере
2. Выберите "Очистить кэш" и "Очистить cookies"
3. Или откройте сайт в режиме инкогнито

## Проверка

Откройте https://businessdb.ru/ и проверьте:
- Русский текст должен отображаться правильно
- В DevTools (F12) → Network → выберите первый запрос → Headers → проверьте `Content-Type: text/html; charset=utf-8`

## Если проблема сохраняется

1. Проверьте логи Apache: `C:\xampp\apache\logs\error.log`
2. Проверьте логи Flask (в консоли где запущен `nssm`)
3. Убедитесь, что в базе данных кодировка Cyrillic_General_CI_AS или UTF-8:

```sql
-- Проверить кодировку БД в MSSQL
SELECT DATABASEPROPERTYEX('buss', 'Collation');
```

Если кодировка базы не UTF-8 и не Cyrillic, данные могут быть повреждены на уровне БД.
