# Настройка Production сайта с HTTPS на Windows 10

## Вариант 1: IIS + wfastcgi (Рекомендуется)

### Шаг 1: Установка компонентов

#### 1.1 Установить IIS (Internet Information Services)

1. Открыть **Панель управления** → **Программы** → **Включение или отключение компонентов Windows**
2. Отметить:
   - ✅ Internet Information Services
   - ✅ Средства веб-управления → Консоль управления IIS
   - ✅ Службы Интернета → Разработка приложений → CGI
   - ✅ Службы Интернета → Безопасность → Фильтрация запросов

#### 1.2 Установить Python компоненты

```cmd
cd C:\путь\к\xbmc
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install wfastcgi
wfastcgi-enable
```

После выполнения `wfastcgi-enable` скопируйте путь (например: `C:\Python311\python.exe|C:\Python311\Lib\site-packages\wfastcgi.py`)

### Шаг 2: Настройка переменных окружения

Создать `.env` файл в корне проекта:

```env
# Безопасность
SECRET_KEY=ваш-сложный-секретный-ключ-минимум-50-символов

# База данных SQLite
DATABASE_URL=sqlite:///instance/xbmc.db

# MS SQL Server
MSSQL_SERVER=172.26.192.1
MSSQL_DATABASE=buss
MSSQL_USERNAME=sa
MSSQL_PASSWORD=123123123
MSSQL_PORT=1433

# ЮKassa (ВАЖНО: использовать домен!)
YUKASSA_SHOP_ID=ваш-shop-id
YUKASSA_SECRET_KEY=ваш-secret-key
YUKASSA_RETURN_URL=https://ваш-домен.ru/payment/success

# Flask режим
FLASK_ENV=production
```

### Шаг 3: Создать web.config

Создать файл `web.config` в корне проекта:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI"
           path="*"
           verb="*"
           modules="FastCgiModule"
           scriptProcessor="C:\Python311\python.exe|C:\Python311\Lib\site-packages\wfastcgi.py"
           resourceType="Unspecified"
           requireAccess="Script" />
    </handlers>

    <rewrite>
      <rules>
        <rule name="Static Files" stopProcessing="true">
          <match url="^static/.*" />
          <action type="Rewrite" url="{R:0}" />
        </rule>
        <rule name="Configure Python" stopProcessing="true">
          <match url="(.*)" />
          <action type="Rewrite" url="run.py/{R:1}" />
        </rule>
      </rules>
    </rewrite>

    <security>
      <requestFiltering>
        <hiddenSegments>
          <add segment=".env" />
          <add segment="venv" />
          <add segment="__pycache__" />
        </hiddenSegments>
      </requestFiltering>
    </security>
  </system.webServer>

  <appSettings>
    <add key="PYTHONPATH" value="C:\путь\к\xbmc" />
    <add key="WSGI_HANDLER" value="run.app" />
    <add key="WSGI_LOG" value="C:\путь\к\xbmc\logs\wfastcgi.log" />
  </appSettings>
</configuration>
```

⚠️ **Замените пути**:
- `C:\Python311\python.exe` → путь к вашему Python
- `C:\Python311\Lib\site-packages\wfastcgi.py` → путь из `wfastcgi-enable`
- `C:\путь\к\xbmc` → реальный путь к проекту

### Шаг 4: Создать сайт в IIS

1. Открыть **Диспетчер служб IIS** (Win+R → `inetmgr`)
2. ПКМ на **Сайты** → **Добавить веб-сайт**
3. Заполнить:
   - **Имя сайта**: XBMC
   - **Физический путь**: `C:\путь\к\xbmc`
   - **Тип**: HTTP
   - **IP-адрес**: Все неназначенные
   - **Порт**: 80
   - **Имя узла**: ваш-домен.ru

4. Нажать **ОК**

### Шаг 5: Настройка SSL (HTTPS)

#### Вариант 5.1: Let's Encrypt (бесплатный, для продакшена)

1. Скачать [win-acme](https://github.com/win-acme/win-acme/releases)
2. Распаковать и запустить `wacs.exe` от имени администратора
3. Выбрать:
   - `N` - Create certificate (simple for IIS)
   - Выбрать ваш сайт из списка
   - Ввести email для уведомлений
   - Подтвердить

Сертификат автоматически установится в IIS и будет обновляться каждые 90 дней.

#### Вариант 5.2: Самоподписанный сертификат (для теста)

1. В **Диспетчере IIS** → **Сертификаты сервера**
2. ПКМ → **Создать самозаверяющий сертификат**
3. Имя: XBMC-SSL
4. Хранилище: Личное

5. Вернуться к сайту → ПКМ → **Изменить привязки**
6. **Добавить**:
   - Тип: HTTPS
   - Порт: 443
   - SSL-сертификат: XBMC-SSL

### Шаг 6: Настройка FastCGI

1. В IIS перейти на уровень сервера
2. Открыть **Параметры FastCGI**
3. Найти запись с Python → **Изменить**
4. Задать:
   - **Максимум экземпляров**: 4
   - **Переменные среды**:
     - `PYTHONPATH` = `C:\путь\к\xbmc`
     - `WSGI_HANDLER` = `run.app`

### Шаг 7: Инициализация базы данных

```cmd
cd C:\путь\к\xbmc
venv\Scripts\activate
python init_db.py
python migrate_ideas_moderation.py
```

### Шаг 8: Перезапуск и проверка

```cmd
# Перезапуск IIS
iisreset

# Или через диспетчер IIS
# ПКМ на сайте → Управление веб-сайтом → Перезапустить
```

Проверить:
- HTTP: `http://ваш-домен.ru`
- HTTPS: `https://ваш-домен.ru`

---

## Вариант 2: Waitress (проще, но без GUI)

### Установка

```cmd
cd C:\путь\к\xbmc
venv\Scripts\activate
pip install waitress
```

### Создать run_production.py

```python
from waitress import serve
from app import create_app
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == '__main__':
    print("Запуск production сервера на порту 8080...")
    serve(app, host='0.0.0.0', port=8080, threads=4)
```

### Запуск как Windows Service

1. Установить **NSSM** (Non-Sucking Service Manager):
   - Скачать: https://nssm.cc/download
   - Распаковать в `C:\nssm`

2. Создать сервис:

```cmd
cd C:\nssm
nssm install XBMC "C:\путь\к\xbmc\venv\Scripts\python.exe" "C:\путь\к\xbmc\run_production.py"
nssm set XBMC AppDirectory "C:\путь\к\xbmc"
nssm set XBMC DisplayName "XBMC Flask Application"
nssm set XBMC Description "Flask приложение для закупок"
nssm set XBMC Start SERVICE_AUTO_START
nssm start XBMC
```

### Настройка Nginx для SSL (Reverse Proxy)

1. Скачать [Nginx для Windows](https://nginx.org/en/download.html)
2. Распаковать в `C:\nginx`
3. Отредактировать `C:\nginx\conf\nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include mime.types;
    default_type application/octet-stream;

    upstream xbmc_backend {
        server 127.0.0.1:8080;
    }

    # HTTP → HTTPS редирект
    server {
        listen 80;
        server_name ваш-домен.ru;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS
    server {
        listen 443 ssl;
        server_name ваш-домен.ru;

        ssl_certificate C:/nginx/ssl/cert.pem;
        ssl_certificate_key C:/nginx/ssl/key.pem;

        location / {
            proxy_pass http://xbmc_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static {
            alias C:/путь/к/xbmc/static;
            expires 30d;
        }
    }
}
```

4. Запустить Nginx:

```cmd
cd C:\nginx
start nginx
```

---

## Проверка настроек

### Тест подключения к MSSQL

```cmd
python -c "from app.mssql import mssql; print(mssql.get_zakupki(limit=1))"
```

### Тест SQLite БД

```cmd
python -c "from app import create_app; from app.models import User; app=create_app(); app.app_context().push(); print(User.query.first())"
```

### Проверка HTTPS

```cmd
curl https://ваш-домен.ru
```

---

## Безопасность

### 1. Firewall (Брандмауэр Windows)

```cmd
# Разрешить HTTP/HTTPS
netsh advfirewall firewall add rule name="HTTP" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="HTTPS" dir=in action=allow protocol=TCP localport=443
```

### 2. Права доступа к файлам

1. ПКМ на папке проекта → **Свойства** → **Безопасность**
2. Добавить пользователя `IIS_IUSRS` с правами:
   - ✅ Чтение
   - ✅ Чтение и выполнение
   - ✅ Список содержимого папки
3. Для папки `instance` (SQLite БД):
   - ✅ Изменение
   - ✅ Запись

### 3. Скрыть заголовки сервера

В `web.config` добавить:

```xml
<httpProtocol>
  <customHeaders>
    <remove name="X-Powered-By" />
    <add name="X-Content-Type-Options" value="nosniff" />
    <add name="X-Frame-Options" value="SAMEORIGIN" />
  </customHeaders>
</httpProtocol>
```

---

## Мониторинг и логи

### Логи IIS
- Расположение: `C:\inetpub\logs\LogFiles\W3SVC1\`
- Формат: W3C Extended Log

### Логи приложения

Создать `logs` папку и настроить в `app/__init__.py`:

```python
import logging
from logging.handlers import RotatingFileHandler
import os

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler(
        'logs/xbmc.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('XBMC startup')
```

---

## Автообновление SSL сертификата (Let's Encrypt)

win-acme автоматически создает задачу в **Планировщике заданий Windows** для обновления каждые 60 дней.

Проверить: **Планировщик заданий** → **win-acme renew**

---

## Troubleshooting

### Ошибка 500 Internal Server Error

1. Проверить логи: `C:\путь\к\xbmc\logs\wfastcgi.log`
2. Проверить права доступа IIS_IUSRS к папке проекта
3. Проверить переменные среды в web.config

### Статические файлы не загружаются

1. В IIS → Сайт → **Параметры обработчиков**
2. Убедиться что StaticFile обработчик активен
3. Проверить путь в `web.config` секции `<rewrite>`

### Платежи не работают

1. Убедиться что `YUKASSA_RETURN_URL` содержит **HTTPS** домен
2. Проверить что домен доступен извне (не localhost)
3. Проверить callback URL в личном кабинете ЮKassa

---

## Резервное копирование

### Создать backup SQLite БД

```cmd
cd C:\путь\к\xbmc
copy instance\xbmc.db backups\xbmc_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db
```

### Создать задачу в Планировщике

1. **Планировщик заданий** → **Создать простую задачу**
2. Триггер: Ежедневно в 3:00
3. Действие: Запуск программы
   - Программа: `cmd.exe`
   - Аргументы: `/c copy C:\путь\к\xbmc\instance\xbmc.db C:\backups\xbmc_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db`

---

## Рекомендации

✅ **Рекомендуется: IIS + wfastcgi + Let's Encrypt**
- Стабильность
- Автообновление SSL
- Интеграция с Windows

✅ **Для простоты: Waitress + Nginx + самоподписанный SSL**
- Быстрая настройка
- Подходит для тестирования

❌ **Не использовать Flask встроенный сервер в продакшене**
- `python run.py` только для разработки!
