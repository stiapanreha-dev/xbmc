# Развертывание на Windows с XAMPP

## Архитектура

```
Интернет → Apache (XAMPP) → Flask приложение
         ↓ порт 80/443      ↓ порт 5000
         SSL сертификат      Python
```

Apache будет работать как reverse proxy, обрабатывая SSL и перенаправляя запросы на Flask.

## Требования

- XAMPP установлен (с Apache)
- Python 3.8+
- SSL сертификат (от Let's Encrypt или другого CA)

## Шаг 1: Настройка Flask приложения

### 1.1 Установка зависимостей

```cmd
cd C:\path\to\xbmc
py -m pip install -r requirements.txt
py -m pip install waitress
```

### 1.2 Создание файла для продакшн запуска

Создайте файл `run_production.py`:

```python
"""
Production server using Waitress (Windows-compatible WSGI server)
"""
from waitress import serve
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))

    print(f"Starting production server on {host}:{port}")
    print("Press Ctrl+C to stop")

    # Waitress - production-ready WSGI server for Windows
    serve(
        app,
        host=host,
        port=port,
        threads=8,  # Количество потоков
        channel_timeout=60,
        cleanup_interval=30,
        _quiet=False
    )
```

### 1.3 Обновление .env

Убедитесь что в `.env` указаны правильные настройки:

```ini
# Flask
SECRET_KEY=your-very-secret-key-change-this
DATABASE_URL=sqlite:///instance/app.db

# MSSQL Server
MSSQL_SERVER=server-address
MSSQL_DATABASE=database-name
MSSQL_USER=username
MSSQL_PASSWORD=password

# Не меняйте - Flask будет слушать только локальные запросы от Apache
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

## Шаг 2: Настройка Apache (XAMPP)

### 2.1 Включение необходимых модулей

Откройте `C:\xampp\apache\conf\httpd.conf` и убедитесь что включены:

```apache
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
LoadModule ssl_module modules/mod_ssl.so
LoadModule rewrite_module modules/mod_rewrite.so
LoadModule headers_module modules/mod_headers.so
```

Раскомментируйте эти строки (уберите `#` в начале).

### 2.2 Настройка виртуального хоста для HTTP (порт 80)

Откройте `C:\xampp\apache\conf\extra\httpd-vhosts.conf` и добавьте:

```apache
<VirtualHost *:80>
    ServerName businessdb.ru
    ServerAlias www.businessdb.ru

    # Редирект всех HTTP запросов на HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]

    ErrorLog "C:/xampp/apache/logs/businessdb-error.log"
    CustomLog "C:/xampp/apache/logs/businessdb-access.log" common
</VirtualHost>
```

### 2.3 Настройка виртуального хоста для HTTPS (порт 443)

Откройте `C:\xampp\apache\conf\extra\httpd-ssl.conf` и добавьте в конец файла:

```apache
<VirtualHost *:443>
    ServerName businessdb.ru
    ServerAlias www.businessdb.ru

    # SSL сертификаты
    SSLEngine on
    SSLCertificateFile "C:/xampp/apache/conf/ssl.crt/businessdb.ru.crt"
    SSLCertificateKeyFile "C:/xampp/apache/conf/ssl.key/businessdb.ru.key"

    # Если есть промежуточные сертификаты (ca-bundle), раскомментируйте:
    # SSLCertificateChainFile "C:/xampp/apache/conf/ssl.crt/businessdb.ru.ca-bundle"

    # Настройки SSL (современные и безопасные)
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5:!3DES
    SSLHonorCipherOrder on

    # Заголовки безопасности
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"

    # Reverse Proxy настройки для Flask
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    # Передача заголовков клиента
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"

    # Логи
    ErrorLog "C:/xampp/apache/logs/businessdb-ssl-error.log"
    CustomLog "C:/xampp/apache/logs/businessdb-ssl-access.log" common
</VirtualHost>
```

### 2.4 Размещение SSL сертификатов

Создайте директории для сертификатов:

```cmd
mkdir C:\xampp\apache\conf\ssl.crt
mkdir C:\xampp\apache\conf\ssl.key
```

Скопируйте файлы сертификата:

**Обязательные файлы:**
- `businessdb.ru.crt` (сертификат) → `C:\xampp\apache\conf\ssl.crt\`
- `businessdb.ru.key` (приватный ключ) → `C:\xampp\apache\conf\ssl.key\`

**Опциональные файлы (если есть):**
- `businessdb.ru.ca-bundle` (цепочка сертификатов) → `C:\xampp\apache\conf\ssl.crt\`

**Важно:** Защитите приватный ключ (.key) от несанкционированного доступа!

**Примечание:** Если у вас только .crt и .key файлы - этого достаточно. CA-bundle нужен только если ваш CA использует промежуточные сертификаты.

## Шаг 3: Автозапуск Flask приложения

### 3.1 Создание Windows Service с помощью NSSM

Скачайте NSSM: https://nssm.cc/download

```cmd
# Распакуйте nssm.exe в C:\nssm\

# Установите Flask как службу
C:\nssm\nssm.exe install FlaskBusinessDB "C:\Python313\python.exe" "C:\path\to\xbmc\run_production.py"

# Настройте рабочую директорию
C:\nssm\nssm.exe set FlaskBusinessDB AppDirectory "C:\path\to\xbmc"

# Настройте автозапуск
C:\nssm\nssm.exe set FlaskBusinessDB Start SERVICE_AUTO_START

# Запустите службу
C:\nssm\nssm.exe start FlaskBusinessDB
```

### 3.2 Альтернатива: BAT файл для запуска

Создайте `start_flask.bat`:

```batch
@echo off
title Flask Business Database
cd /d C:\path\to\xbmc
py run_production.py
pause
```

Добавьте этот файл в автозагрузку Windows:

1. Win + R → `shell:startup`
2. Создайте ярлык на `start_flask.bat`

## Шаг 4: Запуск и проверка

### 4.1 Запуск Flask приложения

**Если используете NSSM:**
```cmd
net start FlaskBusinessDB
```

**Если используете BAT файл:**
```cmd
start_flask.bat
```

Проверьте что Flask работает:
```cmd
curl http://127.0.0.1:5000
```

### 4.2 Перезапуск Apache

Откройте XAMPP Control Panel:
- Stop Apache
- Start Apache

Или через командную строку:
```cmd
net stop Apache2.4
net start Apache2.4
```

### 4.3 Проверка работы

**Локально:**
```cmd
curl http://localhost
curl https://localhost
```

**С другого компьютера:**
```cmd
curl http://businessdb.ru
curl https://businessdb.ru
```

## Шаг 5: Настройка NAT на роутере

Если сервер находится за NAT, настройте проброс портов:

```
Внешний порт 80 → IP сервера:80 (HTTP)
Внешний порт 443 → IP сервера:443 (HTTPS)
```

**Важно:** Удалите старое правило `80 → 5000`, теперь Apache обрабатывает порт 80.

## Мониторинг и обслуживание

### Проверка логов Flask

```cmd
# Смотрите консоль где запущен run_production.py
# Или если используете NSSM:
C:\nssm\nssm.exe status FlaskBusinessDB
```

### Проверка логов Apache

```cmd
type C:\xampp\apache\logs\businessdb-error.log
type C:\xampp\apache\logs\businessdb-ssl-error.log
type C:\xampp\apache\logs\businessdb-access.log
```

### Перезапуск приложения

**Flask (NSSM):**
```cmd
net stop FlaskBusinessDB
net start FlaskBusinessDB
```

**Apache:**
```cmd
net stop Apache2.4
net start Apache2.4
```

## Обновление приложения

```cmd
# 1. Остановите Flask
net stop FlaskBusinessDB

# 2. Обновите код
cd C:\path\to\xbmc
git pull

# 3. Обновите зависимости (если нужно)
py -m pip install -r requirements.txt

# 4. Запустите Flask
net start FlaskBusinessDB
```

Apache не требует перезапуска при обновлении Flask кода.

## Troubleshooting

### Apache не запускается

Проверьте конфигурацию:
```cmd
C:\xampp\apache\bin\httpd.exe -t
```

### Ошибка "SSL Certificate not found"

Проверьте пути к сертификатам в `httpd-ssl.conf`:
```cmd
dir C:\xampp\apache\conf\ssl.crt\businessdb.ru.crt
dir C:\xampp\apache\conf\ssl.key\businessdb.ru.key
```

### Flask не отвечает

Проверьте что приложение запущено:
```cmd
netstat -an | findstr 5000
```

Должна быть строка:
```
TCP    127.0.0.1:5000         0.0.0.0:0              LISTENING
```

### Ошибка 502 Bad Gateway

Apache не может подключиться к Flask. Проверьте:
1. Flask запущен на порту 5000
2. В `.env` указан `FLASK_HOST=127.0.0.1`
3. Firewall не блокирует локальные подключения

### Ошибка "ModuleNotFoundError"

Установите зависимости в правильный Python:
```cmd
py -m pip install -r requirements.txt
```

## Преимущества этого подхода

✅ Apache - проверенный production-ready веб-сервер
✅ Waitress - стабильный WSGI сервер для Windows (заменяет Gunicorn)
✅ SSL обрабатывается Apache (проще настроить)
✅ Логи разделены (Apache + Flask)
✅ Легко масштабируется (можно добавить несколько Flask процессов)
✅ XAMPP Control Panel для удобного управления

## Рекомендации для продакшена

1. **Регулярные бэкапы** базы данных SQLite:
   ```cmd
   copy C:\path\to\xbmc\instance\app.db C:\backups\app_%date%.db
   ```

2. **Ротация логов** Apache (настраивается в httpd.conf):
   ```apache
   ErrorLog "|bin/rotatelogs.exe logs/businessdb-error-%Y-%m-%d.log 86400"
   ```

3. **Мониторинг** (можно использовать Windows Performance Monitor или сторонние инструменты)

4. **Firewall** - разрешите только порты 80 и 443

5. **Автообновление** SSL сертификатов (настройте задачу в Windows Task Scheduler)

## Итоговая структура

```
C:\xampp\
├── apache\
│   ├── conf\
│   │   ├── httpd.conf (включены proxy модули)
│   │   ├── extra\
│   │   │   ├── httpd-vhosts.conf (настроен редирект HTTP→HTTPS)
│   │   │   └── httpd-ssl.conf (настроен reverse proxy)
│   │   └── ssl.crt\
│   │       ├── businessdb.ru.crt
│   │       └── businessdb.ru.ca-bundle
│   └── ssl.key\
│       └── businessdb.ru.key
│
C:\path\to\xbmc\
├── app\
├── templates\
├── static\
├── .env (настройки подключения)
├── run_production.py (Waitress сервер)
└── requirements.txt
```
