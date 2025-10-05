# Настройка SSL для businessdb.ru

## Текущая ситуация

**Домен**: businessdb.ru
**IP**: 176.117.212.121
**Проблема**: Порт 443 открыт, но SSL handshake завершается ошибкой

```
HTTP (порт 80): ✅ Работает (Flask через Werkzeug)
HTTPS (порт 443): ❌ Ошибка SSL handshake
```

## Диагностика

Ошибка при подключении:
```
OpenSSL: error:0A000126:SSL routines::unexpected eof while reading
```

Это означает, что сервер обрывает соединение до завершения TLS handshake.

## Возможные причины

1. **SSL сертификат не установлен** на порт 443
2. **Неправильная конфигурация** веб-сервера (Apache/Nginx/IIS)
3. **Flask работает напрямую** без reverse proxy
4. **Самоподписанный сертификат** с проблемами
5. **Файрвол** блокирует SSL трафик

## Решение 1: Установка бесплатного SSL сертификата (Let's Encrypt)

### Для Linux (Ubuntu/Debian)

```bash
# 1. Установить Certbot
sudo apt update
sudo apt install certbot python3-certbot-apache  # для Apache
# или
sudo apt install certbot python3-certbot-nginx   # для Nginx

# 2. Получить и установить сертификат
sudo certbot --apache -d businessdb.ru -d www.businessdb.ru  # для Apache
# или
sudo certbot --nginx -d businessdb.ru -d www.businessdb.ru   # для Nginx

# 3. Автоматическое обновление сертификата
sudo certbot renew --dry-run
```

### Для Windows (с IIS или Apache)

#### Вариант A: Certbot для Windows

1. Скачать Certbot: https://dl.eff.org/certbot-beta-installer-win_amd64_signed.exe
2. Установить
3. Открыть PowerShell от администратора:
   ```powershell
   certbot certonly --standalone -d businessdb.ru -d www.businessdb.ru
   ```
4. Сертификаты будут в: `C:\Certbot\live\businessdb.ru\`

#### Вариант B: Win-ACME (проще для Windows)

1. Скачать: https://www.win-acme.com/
2. Распаковать и запустить `wacs.exe`
3. Выбрать "N: Create certificate (full options)"
4. Следовать инструкциям для IIS или Apache

## Решение 2: Настройка Apache с SSL (рекомендуется)

### Конфигурация Apache для businessdb.ru

**Файл**: `/etc/apache2/sites-available/businessdb.ru-ssl.conf` (Linux)
или `C:\Apache24\conf\extra\httpd-vhosts.conf` (Windows)

```apache
<VirtualHost *:80>
    ServerName businessdb.ru
    ServerAlias www.businessdb.ru

    # Перенаправление на HTTPS
    Redirect permanent / https://businessdb.ru/
</VirtualHost>

<VirtualHost *:443>
    ServerName businessdb.ru
    ServerAlias www.businessdb.ru

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/privkey.pem
    SSLCertificateChainFile /path/to/chain.pem

    # Современные настройки SSL
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5:!3DES
    SSLHonorCipherOrder on

    # Proxy к Flask приложению
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    # Логи
    ErrorLog ${APACHE_LOG_DIR}/businessdb-error.log
    CustomLog ${APACHE_LOG_DIR}/businessdb-access.log combined
</VirtualHost>
```

### Включение модулей Apache

```bash
# Linux
sudo a2enmod ssl
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo a2ensite businessdb.ru-ssl.conf
sudo systemctl restart apache2

# Windows
# Раскомментировать в httpd.conf:
LoadModule ssl_module modules/mod_ssl.so
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
```

## Решение 3: Настройка Nginx с SSL

**Файл**: `/etc/nginx/sites-available/businessdb.ru`

```nginx
# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name businessdb.ru www.businessdb.ru;

    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name businessdb.ru www.businessdb.ru;

    # SSL Configuration
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Proxy to Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Логи
    access_log /var/log/nginx/businessdb-access.log;
    error_log /var/log/nginx/businessdb-error.log;
}
```

Включить конфигурацию:
```bash
sudo ln -s /etc/nginx/sites-available/businessdb.ru /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Решение 4: Проверка текущей конфигурации

### Определить, что установлено на сервере

```bash
# Проверить Apache
sudo systemctl status apache2   # Linux
netstat -ano | findstr :443      # Windows

# Проверить Nginx
sudo systemctl status nginx

# Проверить IIS (Windows)
Get-Service W3SVC

# Проверить, что слушает порт 443
sudo netstat -tulpn | grep :443  # Linux
netstat -ano | findstr :443      # Windows
```

### Проверить логи

```bash
# Apache (Linux)
sudo tail -f /var/log/apache2/error.log

# Apache (Windows)
type C:\Apache24\logs\error.log

# Nginx
sudo tail -f /var/log/nginx/error.log
```

## Решение 5: Временное решение - Flask с SSL (НЕ для продакшена!)

Если нужно быстро проверить SSL, можно запустить Flask со встроенным SSL:

**Файл**: `run_ssl.py`
```python
from app import create_app
import ssl

app = create_app()

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('path/to/cert.pem', 'path/to/key.pem')

    app.run(
        host='0.0.0.0',
        port=443,
        ssl_context=context
    )
```

⚠️ **Внимание**: Это только для тестирования! В продакшене используйте Apache/Nginx.

## Проверка после настройки

1. **Проверить SSL сертификат**:
   ```bash
   openssl s_client -connect businessdb.ru:443 -servername businessdb.ru
   ```

2. **Проверить в браузере**:
   - Откройте https://businessdb.ru
   - Проверьте значок замка в адресной строке
   - Сертификат должен быть действительным

3. **Онлайн проверка SSL**:
   - https://www.ssllabs.com/ssltest/analyze.html?d=businessdb.ru

## Что нужно сделать СЕЙЧАС

### Шаг 1: Определить конфигурацию сервера

Выполните на сервере и отправьте результаты:

```bash
# Какая ОС?
cat /etc/os-release      # Linux
systeminfo               # Windows

# Что слушает порт 443?
sudo netstat -tulpn | grep :443   # Linux
netstat -ano | findstr :443       # Windows

# Какой веб-сервер?
apache2 -v               # Linux
httpd -v                 # Windows Apache
nginx -v
```

### Шаг 2: Проверить наличие сертификата

```bash
# Найти сертификаты
sudo find / -name "*.crt" -o -name "*.pem" 2>/dev/null | grep -i businessdb

# Проверить Let's Encrypt
sudo ls -la /etc/letsencrypt/live/
```

### Шаг 3: Предоставить доступ

Для настройки SSL нужен доступ к серверу через SSH (инструкция в `setup_ssh_windows.ps1`).

## Контрольный список

- [ ] Определить ОС сервера (Linux/Windows)
- [ ] Определить веб-сервер (Apache/Nginx/IIS)
- [ ] Проверить наличие SSL сертификата
- [ ] Получить или создать сертификат (Let's Encrypt)
- [ ] Настроить веб-сервер для SSL
- [ ] Настроить редирект HTTP → HTTPS
- [ ] Настроить proxy к Flask приложению
- [ ] Проверить работу HTTPS
- [ ] Настроить автообновление сертификата

## Следующие шаги

1. **Срочно**: Предоставить SSH доступ для диагностики
2. Определить текущую конфигурацию сервера
3. Установить/исправить SSL сертификат
4. Настроить веб-сервер правильно
5. Протестировать HTTPS подключение

## Команды для быстрой диагностики

Выполните на сервере и отправьте результаты:

```bash
#!/bin/bash
echo "=== OS INFO ==="
cat /etc/os-release 2>/dev/null || systeminfo

echo -e "\n=== LISTENING PORTS ==="
sudo netstat -tulpn | grep -E ':80|:443' 2>/dev/null || netstat -ano | findstr -E ":80 :443"

echo -e "\n=== WEB SERVERS ==="
apache2 -v 2>/dev/null || httpd -v 2>/dev/null || echo "Apache not found"
nginx -v 2>/dev/null || echo "Nginx not found"

echo -e "\n=== SSL CERTIFICATES ==="
sudo ls -la /etc/letsencrypt/live/ 2>/dev/null || echo "No Let's Encrypt certs"
sudo ls -la /etc/ssl/certs/ 2>/dev/null | grep -i businessdb || echo "No businessdb certs"

echo -e "\n=== PROCESSES ON PORT 443 ==="
sudo lsof -i :443 2>/dev/null || netstat -ano | findstr :443
```

Сохраните вывод и отправьте для анализа.
