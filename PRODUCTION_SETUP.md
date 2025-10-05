# Настройка продакшен окружения для businessdb.ru

## Архитектура с NAT

```
Интернет → Роутер → Сервер
           (NAT)

Порт 80  → 80   → Gunicorn (HTTP на порту 80)
Порт 443 → 443  → Gunicorn (HTTPS на порту 443)
```

## Вариант 1: Gunicorn с SSL (Рекомендуется)

### Шаг 1: Установка зависимостей

```bash
# Linux/WSL
pip install gunicorn gevent

# Windows
pip install gunicorn gevent pywin32
```

### Шаг 2: Размещение SSL сертификатов

Создайте папку для сертификатов:
```bash
mkdir -p /home/lexun/work/KWORK/xbmc/cert
# или для Windows
mkdir C:\path\to\xbmc\cert
```

Разместите файлы:
- `cert/certificate.crt` или `cert/fullchain.pem` - сертификат
- `cert/private.key` или `cert/privkey.pem` - приватный ключ

### Шаг 3: Конфигурация Gunicorn

**Файл**: `gunicorn_config.py`

```python
import multiprocessing
import os

# Базовая конфигурация
bind = "0.0.0.0:443"  # HTTPS порт
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 5

# SSL Configuration
certfile = os.path.join(os.path.dirname(__file__), 'cert', 'fullchain.pem')
keyfile = os.path.join(os.path.dirname(__file__), 'cert', 'privkey.pem')

# Для Windows используйте абсолютные пути:
# certfile = r'C:\path\to\xbmc\cert\certificate.crt'
# keyfile = r'C:\path\to\xbmc\cert\private.key'

# Логирование
accesslog = 'logs/gunicorn-access.log'
errorlog = 'logs/gunicorn-error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Безопасность
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Процесс
daemon = False  # Для Windows должно быть False
pidfile = 'gunicorn.pid'
user = None  # Только для Linux
group = None  # Только для Linux

# SSL настройки (дополнительно)
ssl_version = 5  # TLS 1.2 minimum
ciphers = 'TLSv1.2:TLSv1.3'
```

### Шаг 4: Запуск Gunicorn

**Linux/WSL:**
```bash
# Создать папку для логов
mkdir -p logs

# Запуск с SSL
gunicorn -c gunicorn_config.py "app:create_app()"

# Или напрямую с параметрами
gunicorn \
  --bind 0.0.0.0:443 \
  --workers 4 \
  --worker-class gevent \
  --certfile cert/fullchain.pem \
  --keyfile cert/privkey.pem \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  "app:create_app()"
```

**Windows:**
```cmd
REM Создать папку для логов
mkdir logs

REM Запуск
gunicorn -c gunicorn_config.py "app:create_app()"
```

### Шаг 5: Создание службы Windows

**Файл**: `install_windows_service.py`

```python
import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import os
import sys

class GunicornService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BusinessDatabaseService"
    _svc_display_name_ = "Business Database (Gunicorn)"
    _svc_description_ = "Production Flask application with Gunicorn"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        # Путь к проекту
        app_dir = r'C:\path\to\xbmc'  # ИЗМЕНИТЬ!
        os.chdir(app_dir)

        # Запуск Gunicorn
        cmd = [
            'gunicorn',
            '-c', 'gunicorn_config.py',
            'app:create_app()'
        ]

        self.process = subprocess.Popen(cmd)
        self.process.wait()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(GunicornService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(GunicornService)
```

**Установка службы:**
```cmd
REM Установить
python install_windows_service.py install

REM Запустить
python install_windows_service.py start

REM Остановить
python install_windows_service.py stop

REM Удалить
python install_windows_service.py remove
```

### Шаг 6: Настройка NAT на роутере

В настройках роутера создайте правила:

```
Внешний порт 80  → IP сервера:80  (HTTP - опционально)
Внешний порт 443 → IP сервера:443 (HTTPS)
```

### Шаг 7: Настройка брандмауэра Windows

```powershell
# Разрешить порт 443
New-NetFirewallRule -DisplayName "Business Database HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow

# Разрешить порт 80 (опционально)
New-NetFirewallRule -DisplayName "Business Database HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
```

## Вариант 2: Двойной запуск Gunicorn (HTTP + HTTPS)

Если нужны оба порта одновременно.

### Конфигурация для HTTP (порт 80)

**Файл**: `gunicorn_http.py`

```python
import multiprocessing

bind = "0.0.0.0:80"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
accesslog = 'logs/gunicorn-http-access.log'
errorlog = 'logs/gunicorn-http-error.log'
loglevel = 'info'
```

### Конфигурация для HTTPS (порт 443)

**Файл**: `gunicorn_https.py`

```python
import multiprocessing
import os

bind = "0.0.0.0:443"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"

certfile = 'cert/fullchain.pem'
keyfile = 'cert/privkey.pem'

accesslog = 'logs/gunicorn-https-access.log'
errorlog = 'logs/gunicorn-https-error.log'
loglevel = 'info'
```

### Запуск обоих серверов

**Linux/WSL (supervisor):**

Установите supervisor:
```bash
sudo apt install supervisor
```

**Файл**: `/etc/supervisor/conf.d/businessdb.conf`

```ini
[program:businessdb-http]
command=/home/lexun/.local/bin/gunicorn -c gunicorn_http.py "app:create_app()"
directory=/home/lexun/work/KWORK/xbmc
user=lexun
autostart=true
autorestart=true
stderr_logfile=/var/log/businessdb-http.err.log
stdout_logfile=/var/log/businessdb-http.out.log

[program:businessdb-https]
command=/home/lexun/.local/bin/gunicorn -c gunicorn_https.py "app:create_app()"
directory=/home/lexun/work/KWORK/xbmc
user=lexun
autostart=true
autorestart=true
stderr_logfile=/var/log/businessdb-https.err.log
stdout_logfile=/var/log/businessdb-https.out.log
```

Запуск:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start businessdb-http businessdb-https
```

**Windows (два отдельных скрипта):**

**Файл**: `start_http.bat`
```batch
@echo off
cd /d %~dp0
gunicorn -c gunicorn_http.py "app:create_app()"
```

**Файл**: `start_https.bat`
```batch
@echo off
cd /d %~dp0
gunicorn -c gunicorn_https.py "app:create_app()"
```

Запускайте оба скрипта в отдельных окнах или создайте две службы Windows.

## Вариант 3: Редирект HTTP → HTTPS в приложении

Добавьте в `app/__init__.py`:

```python
from flask import Flask, request, redirect

def create_app():
    app = Flask(__name__)

    # ... существующая конфигурация ...

    # Редирект HTTP → HTTPS
    @app.before_request
    def before_request():
        if not request.is_secure and request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

    # ... остальной код ...

    return app
```

## Проверка работы

### 1. Локальная проверка

```bash
# Проверить HTTPS
curl -k https://localhost:443

# Проверить HTTP (если запущен)
curl http://localhost:80
```

### 2. Внешняя проверка

```bash
# Проверить домен
curl -I https://businessdb.ru

# Проверить сертификат
openssl s_client -connect businessdb.ru:443 -servername businessdb.ru
```

### 3. Проверка в браузере

Откройте https://businessdb.ru и проверьте:
- ✅ Замок в адресной строке (сертификат валиден)
- ✅ Приложение работает
- ✅ HTTP редиректит на HTTPS (если настроен)

## Получение SSL сертификата (Let's Encrypt)

### Вариант A: Certbot (для автоматического обновления)

**Windows:**
```powershell
# Скачать Certbot
# https://dl.eff.org/certbot-beta-installer-win_amd64_signed.exe

# Получить сертификат (standalone режим, порты должны быть свободны!)
certbot certonly --standalone -d businessdb.ru -d www.businessdb.ru

# Сертификаты будут в: C:\Certbot\live\businessdb.ru\
# Скопировать в проект:
Copy-Item C:\Certbot\live\businessdb.ru\fullchain.pem cert\
Copy-Item C:\Certbot\live\businessdb.ru\privkey.pem cert\
```

**Linux:**
```bash
# Установить Certbot
sudo apt install certbot

# Получить сертификат
sudo certbot certonly --standalone -d businessdb.ru -d www.businessdb.ru

# Скопировать в проект
sudo cp /etc/letsencrypt/live/businessdb.ru/fullchain.pem cert/
sudo cp /etc/letsencrypt/live/businessdb.ru/privkey.pem cert/
sudo chown lexun:lexun cert/*.pem
```

### Вариант B: Использование существующего сертификата

Если у клиента уже есть сертификат, просто скопируйте файлы в `cert/`:
```
cert/certificate.crt (или fullchain.pem)
cert/private.key (или privkey.pem)
cert/ca_bundle.crt (опционально)
```

## Автоматическое обновление Let's Encrypt

### Windows (Task Scheduler)

Создайте задачу в планировщике:
1. Открыть "Планировщик заданий"
2. Создать задачу → "Выполнять раз в месяц"
3. Действие: `certbot renew --quiet`
4. После обновления: скопировать сертификаты и перезапустить службу

**PowerShell скрипт** `renew_cert.ps1`:
```powershell
# Обновить сертификат
certbot renew --quiet

# Скопировать новые файлы
Copy-Item C:\Certbot\live\businessdb.ru\fullchain.pem C:\path\to\xbmc\cert\ -Force
Copy-Item C:\Certbot\live\businessdb.ru\privkey.pem C:\path\to\xbmc\cert\ -Force

# Перезапустить службу
Restart-Service BusinessDatabaseService
```

### Linux (Cron)

```bash
# Добавить в crontab
sudo crontab -e

# Проверка обновления каждый день в 3:00
0 3 * * * certbot renew --quiet --deploy-hook "systemctl restart businessdb"
```

## Мониторинг и логи

### Просмотр логов Gunicorn

```bash
# Linux
tail -f logs/gunicorn-access.log
tail -f logs/gunicorn-error.log

# Windows
Get-Content logs\gunicorn-access.log -Wait
Get-Content logs\gunicorn-error.log -Wait
```

### Проверка статуса службы (Windows)

```powershell
Get-Service BusinessDatabaseService
sc query BusinessDatabaseService
```

### Проверка процессов

```bash
# Linux
ps aux | grep gunicorn
netstat -tulpn | grep :443

# Windows
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
netstat -ano | findstr :443
```

## Решение проблем

### Ошибка: "Address already in use"

Порт 443 занят другим процессом:
```bash
# Найти процесс
sudo lsof -i :443  # Linux
netstat -ano | findstr :443  # Windows

# Остановить процесс
sudo kill -9 PID  # Linux
taskkill /PID xxxx /F  # Windows
```

### Ошибка: "Permission denied" (порт < 1024)

**Linux**: Нужны права root для портов < 1024
```bash
# Вариант 1: Запуск с sudo (не рекомендуется)
sudo gunicorn ...

# Вариант 2: Дать права на привязку к порту
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3.x

# Вариант 3: Использовать порт > 1024 и настроить iptables
gunicorn --bind 0.0.0.0:8443 ...
sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8443
```

**Windows**: Запустить от администратора

### Сертификат не работает

Проверьте пути к файлам:
```python
import os
print(os.path.abspath('cert/fullchain.pem'))
print(os.path.exists('cert/fullchain.pem'))
```

## Итоговая команда для запуска (ПРОДАКШЕН)

**Linux/WSL:**
```bash
gunicorn \
  --bind 0.0.0.0:443 \
  --workers 4 \
  --worker-class gevent \
  --certfile cert/fullchain.pem \
  --keyfile cert/privkey.pem \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  "app:create_app()"
```

**Windows:**
```cmd
gunicorn -c gunicorn_config.py "app:create_app()"
```

**Настройка NAT:**
```
Роутер: Внешний порт 443 → IP сервера:443
```

Всё готово для продакшена! 🚀
