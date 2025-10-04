# Быстрый старт - Развертывание из GitHub

> **Для Windows 10/11** - используйте PowerShell или Command Prompt

## Требования

- **Python 3.8+** - [скачать](https://www.python.org/downloads/)
- **Git** - [скачать](https://git-scm.com/download/win)
- **MS SQL Server** (должен быть установлен и запущен)

## 1. Клонирование репозитория

**PowerShell / CMD:**
```cmd
git clone https://github.com/stiapanreha-dev/xbmc.git
cd xbmc
```

## 2. Установка зависимостей

```cmd
pip install -r requirements.txt
```

*Если pip не найден, используйте:* `python -m pip install -r requirements.txt`

## 3. Настройка переменных окружения

Создайте файл `.env`:

**PowerShell:**
```powershell
Copy-Item .env.example .env
```

**CMD:**
```cmd
copy .env.example .env
```

Откройте файл `.env` в блокноте и укажите настройки:

```env
# Обязательные настройки
SECRET_KEY=your-random-secret-key-here
DATABASE_URL=sqlite:///xbmc.db

# MS SQL Server
# Если SQL Server на этом же компьютере, используйте localhost или 127.0.0.1
MSSQL_SERVER=localhost
MSSQL_USER=sa
MSSQL_PASSWORD=ваш-пароль-sql
MSSQL_DATABASE=buss
MSSQL_PORT=1433

# Email (для верификации пользователей)
SMTP_HOST=smtp.timeweb.ru
SMTP_PORT=465
SMTP_USER=info@businessdb.ru
SMTP_PASSWORD=608sV0i22
FROM_EMAIL=info@businessdb.ru
FROM_NAME=XBMC

# SMS.ru (для верификации телефона)
SMSRU_API_KEY=20AC889F-40E9-8B3B-1D7A-94042CFC03B5
SMSRU_FROM_NAME=

# ЮKassa (опционально, для тестирования используйте значения ниже)
YUKASSA_SHOP_ID=test-shop-id
YUKASSA_SECRET_KEY=test-secret-key
YUKASSA_RETURN_URL=http://localhost:5000/payment/success
```

## 4. Инициализация базы данных

```cmd
python scripts\init_db.py
```

Будет создан админ пользователь:
- **Логин:** admin
- **Пароль:** admin123

## 5. Запуск приложения

```cmd
python run.py
```

Приложение доступно по адресу: **http://localhost:5000**

Откройте браузер и перейдите по адресу `http://localhost:5000`

## 6. Проверка подключения к MS SQL

Создайте файл `test_connection.py`:

```python
from app.mssql import mssql

try:
    result = mssql.get_zakupki(limit=1)
    print(f'✓ Подключено! Записей: {result["total"]}')
except Exception as e:
    print(f'✗ Ошибка: {e}')
```

Запустите:
```cmd
python test_connection.py
```

## 7. Тестирование сервисов (опционально)

### Email сервис:
```cmd
python tests\test_email_service.py
```

### SMS сервис:
```cmd
python tests\test_sms_service.py
```

## 8. Публичный доступ через ngrok (опционально)

Если нужен доступ из интернета:

1. Скачайте ngrok: https://ngrok.com/download
2. Распакуйте `ngrok.exe`
3. Запустите в отдельном окне CMD:

```cmd
ngrok http 5000
```

Получите публичный URL вида: `https://xxxxx.ngrok-free.app`

---

## Важные примечания

### MS SQL Server (Windows)

**Проверка, что SQL Server запущен:**
1. Нажмите `Win + R`, введите `services.msc`
2. Найдите **SQL Server (SQLEXPRESS)** или **SQL Server (MSSQLSERVER)**
3. Убедитесь, что статус: **Running**

**Если нужно включить TCP/IP:**
1. Откройте **SQL Server Configuration Manager**
2. **SQL Server Network Configuration** → **Protocols for SQLEXPRESS**
3. ПКМ на **TCP/IP** → **Enable**
4. Перезапустите службу SQL Server

**Узнать пароль пользователя sa:**
Если не помните пароль, можно сбросить через SSMS с Windows Authentication

### Email/SMS верификация
- Email работает только если SMTP сервер доступен с вашего IP
- Если используете VPN, добавьте исключение для smtp.timeweb.ru
- SMS отправляются через API SMS.ru (проверьте баланс)
- Админ пользователь создается с уже подтвержденными email и телефоном

### Демо режим оплаты
При использовании `YUKASSA_SHOP_ID=test-shop-id` активируется демо режим - баланс пополняется мгновенно без реальной оплаты.

---

## Структура проекта

```
xbmc/
├── app/                    # Код приложения
│   ├── routes/            # Маршруты (auth, main, payment)
│   ├── models.py          # Модели БД
│   ├── email_service.py   # Email сервис
│   └── sms_service.py     # SMS сервис
├── scripts/               # Служебные скрипты
│   └── init_db.py        # Инициализация БД
├── tests/                 # Тесты
├── templates/             # HTML шаблоны
├── static/                # CSS, JS, изображения
├── .env                   # Настройки (создайте из .env.example)
└── run.py                # Точка входа

```

## Возможные проблемы

### Ошибка подключения к MS SQL
```
✗ Unable to connect: Adaptive Server is unavailable
```
**Решение:** Проверьте IP адрес, порт и что SQL Server запущен

### Ошибка аутентификации
```
✗ Login failed for user 'sa'
```
**Решение:** Проверьте логин/пароль в .env, включите SQL Server Authentication

### Email не приходит
**Решение:** См. файл `.scripts/EMAIL_ISSUE.md` для диагностики SMTP

### Модуль не найден
```
ModuleNotFoundError: No module named 'XXX'
```
**Решение:** `pip install -r requirements.txt`

---

---

## ⚡ Быстрый чеклист

Для опытных пользователей - вся установка в 5 командах:

```cmd
git clone https://github.com/stiapanreha-dev/xbmc.git
cd xbmc
pip install -r requirements.txt
copy .env.example .env
REM Отредактируйте .env с вашими настройками SQL
python scripts\init_db.py
python run.py
```

Откройте http://localhost:5000 и войдите как **admin/admin123**

---

## Дополнительная документация

- **INSTALL.md** - Подробная инструкция по установке и настройке SQL Server
- **CLAUDE.md** - Техническая документация проекта
- **PRODUCTION_WINDOWS.md** - Развертывание на Windows Server
- **.scripts/EMAIL_ISSUE.md** - Диагностика проблем с email

## Поддержка

- Telegram: @cdvks
- Repository: https://github.com/stiapanreha-dev/xbmc
