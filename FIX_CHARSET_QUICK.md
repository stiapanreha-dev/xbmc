# Быстрое исправление кодировки (для клиента)

## Проблема
Русский текст отображается как кракозябры. Причина: база данных MSSQL хранит данные в кодировке Windows-1251, а приложение пыталось читать как UTF-8.

## Решение
Изменена кодировка подключения к MSSQL с `utf8` на `cp1251`.

## Что делать

### 1. Обновите код

```powershell
cd C:\soft\business.db
git pull origin master
```

Если git не установлен:
```powershell
winget install --id Git.Git -e
```

### 2. Перезапустите Flask сервис

```powershell
nssm restart flask_app
```

### 3. Проверьте результат

Откройте https://businessdb.ru/ или http://localhost:5000/ - русский текст должен отображаться правильно.

## Если не помогло

Попробуйте другие варианты кодировки в файле `.env`:

```bash
# Вариант 1 (по умолчанию)
MSSQL_CHARSET=cp1251

# Вариант 2
MSSQL_CHARSET=utf8

# Вариант 3
MSSQL_CHARSET=UTF-8
```

После изменения `.env` не забудьте перезапустить сервис:
```powershell
nssm restart flask_app
```

## Проверка кодировки базы данных

Если ничего не помогло, проверьте кодировку в SQL Server Management Studio:

```sql
SELECT DATABASEPROPERTYEX('buss', 'Collation');
```

Если результат содержит `Cyrillic_General` - используйте `MSSQL_CHARSET=cp1251`
Если результат содержит `UTF8` - используйте `MSSQL_CHARSET=utf8`
