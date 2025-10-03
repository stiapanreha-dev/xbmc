# Инструкция по развертыванию проекта XBMC

## Требования

### Серверная часть (Linux/WSL)
- Python 3.8+
- pip
- Доступ к MS SQL Server

### База данных (Windows)
- MS SQL Server 2019+ или SQL Server Express
- SQL Server Management Studio (SSMS)

## Шаг 1: Распаковка архива

Распакуйте архив в нужную директорию:
```bash
unzip xbmc.zip
cd xbmc
```

## Шаг 2: Создание виртуального окружения (рекомендуется)

```bash
python3 -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

## Шаг 3: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 4: Настройка MS SQL Server (Windows)

> **Примечание:** Предполагается, что MS SQL Server уже установлен. Ниже приведены дополнительные настройки, которые могут потребоваться.

### 4.1. Настройка SQL Server Authentication (если требуется)

1. Откройте SSMS и подключитесь к серверу
2. ПКМ на сервере → **Properties** → **Security**
3. Выберите **SQL Server and Windows Authentication mode**
4. Нажмите **OK**

### 4.2. Создание пользователя SQL (если требуется)

Если у вас нет пользователя для подключения или нужно создать нового:

1. В SSMS: **Security** → **Logins** → ПКМ **New Login**
2. Login name: `sa` (или свой)
3. Выберите **SQL Server authentication**
4. Введите пароль
5. Снимите галочку **Enforce password policy** (для упрощения)
6. Перейдите на вкладку **Server Roles**
7. Поставьте галочку **sysadmin**
8. Нажмите **OK**

Или используйте SQL команду:
```sql
ALTER LOGIN sa ENABLE;
GO
ALTER LOGIN sa WITH PASSWORD = 'YourPassword123';
GO
```

### 4.3. Включение TCP/IP (если требуется)

1. Откройте **SQL Server Configuration Manager**
2. **SQL Server Network Configuration** → **Protocols for SQLEXPRESS**
3. ПКМ на **TCP/IP** → **Enable**
4. ПКМ на **TCP/IP** → **Properties** → вкладка **IP Addresses**
5. Прокрутите до **IPAll**
6. **TCP Port**: `1433`
7. Нажмите **OK**

### 4.4. Перезапуск службы SQL Server

После изменения настроек TCP/IP перезапустите службу:

1. В Configuration Manager: **SQL Server Services**
2. ПКМ на **SQL Server (SQLEXPRESS)** → **Restart**

### 4.5. Открытие порта в брандмауэре Windows (если требуется)

**Вариант 1 - через PowerShell (от администратора):**
```powershell
New-NetFirewallRule -DisplayName "SQL Server Port 1433" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 1433 `
    -Action Allow
```

**Вариант 2 - через GUI:**
1. **Windows Defender Firewall** → **Advanced Settings**
2. **Inbound Rules** → **New Rule**
3. **Port** → Next
4. **TCP**, Specific ports: `1433` → Next
5. **Allow the connection** → Next
6. Отметьте все (Domain, Private, Public) → Next
7. Name: `SQL Server` → Finish

### 4.6. Узнайте IP адрес Windows машины

Откройте CMD и выполните:
```cmd
ipconfig
```
Запомните **IPv4 Address** (например, `192.168.1.100`)

## Шаг 5: Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Секретный ключ Flask (измените на свой!)
SECRET_KEY=your-random-secret-key-here

# SQLite база для пользователей и настроек
DATABASE_URL=sqlite:///xbmc.db

# Настройки ЮKassa (если используется реальная оплата)
YUKASSA_SHOP_ID=your-shop-id
YUKASSA_SECRET_KEY=your-secret-key
YUKASSA_RETURN_URL=http://your-domain.com/payment/success

# Настройки подключения к MS SQL Server
MSSQL_SERVER=192.168.1.100  # IP адрес Windows машины
MSSQL_USER=sa                # Имя пользователя SQL
MSSQL_PASSWORD=your-password # Пароль от SQL
MSSQL_DATABASE=buss          # Имя базы данных
MSSQL_PORT=1433
```

**Важно:**
- Замените `192.168.1.100` на реальный IP вашего SQL Server
- Замените `your-password` на пароль пользователя `sa`
- Если SQL Server на той же машине, можно использовать `localhost` или `127.0.0.1`
- Если используете WSL, узнайте IP хоста: `cat /etc/resolv.conf | grep nameserver | awk '{print $2}'`

## Шаг 6: Инициализация локальной базы данных

Инициализируйте SQLite базу для пользователей:

```bash
python3 init_db.py
```

Будет создан тестовый пользователь:
- Логин: `admin`
- Пароль: `admin123`

## Шаг 7: Запуск приложения

```bash
python3 run.py
```

Приложение будет доступно по адресу: http://localhost:5000

## Шаг 8: Настройка ngrok (опционально, для публичного доступа)

### 8.1. Установка ngrok

1. Скачайте ngrok: https://ngrok.com/download
2. Распакуйте и добавьте в PATH

### 8.2. Запуск ngrok

В отдельном терминале:
```bash
ngrok http 5000
```

Вы получите публичный URL, например: `https://abc123.ngrok.io`

## Проверка подключения к MSSQL

Проверьте, что приложение может подключиться к SQL Server:

```bash
python3 << 'EOF'
from app.mssql import mssql
try:
    result = mssql.get_zakupki(limit=1)
    print(f"✓ Подключение успешно! Найдено записей: {result['total']}")
except Exception as e:
    print(f"✗ Ошибка подключения: {e}")
EOF
```

## Структура проекта

```
xbmc/
├── app/
│   ├── __init__.py          # Инициализация Flask приложения
│   ├── models.py            # Модели SQLite (пользователи, новости)
│   ├── mssql.py             # Подключение к MSSQL
│   └── routes/
│       ├── main.py          # Основные маршруты
│       ├── auth.py          # Авторизация
│       └── payment.py       # Оплата
├── static/
│   ├── css/style.css        # Стили
│   └── js/main.js           # JavaScript
├── templates/               # HTML шаблоны
├── .env                     # Настройки (не в git!)
├── .env.example             # Пример настроек
├── requirements.txt         # Зависимости Python
├── run.py                   # Точка входа
├── init_db.py              # Инициализация SQLite БД
└── README.md               # Основная документация

## Возможные проблемы

### Ошибка подключения к SQL Server

**Симптом:** `Unable to connect: Adaptive Server is unavailable`

**Решение:**
1. Проверьте, что SQL Server запущен
2. Проверьте IP адрес в `.env`
3. Проверьте, что порт 1433 открыт в брандмауэре
4. Проверьте, что TCP/IP включен в SQL Server Configuration Manager

### Ошибка аутентификации SQL

**Симптом:** `Login failed for user 'sa'`

**Решение:**
1. Проверьте логин и пароль в `.env`
2. Убедитесь, что включена SQL Server Authentication
3. Перезапустите SQL Server после изменения настроек

### Модуль не найден

**Симптом:** `ModuleNotFoundError: No module named 'XXX'`

**Решение:**
```bash
pip install -r requirements.txt
```

## Производственное развертывание

Для production окружения:

1. Используйте gunicorn вместо встроенного сервера Flask:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

2. Настройте nginx как reverse proxy
3. Используйте SSL сертификат
4. Смените `SECRET_KEY` на случайную строку
5. Отключите `debug=True` в `run.py`
6. Настройте логирование
7. Используйте PostgreSQL вместо SQLite для пользователей

## Поддержка

По вопросам обращайтесь:
- Email: support@xbmc.ru
- Telegram: @cdvks
