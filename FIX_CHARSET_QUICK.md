# Быстрое исправление кодировки (для клиента)

## Проблема
Русский текст в колонке "Цена контракта" отображается как кракозябры.

**Причина:** SQL Server выполнял CAST в VARCHAR с собственной кодировкой, а затем Python читал с другой кодировкой (cp1251), что приводило к двойному преобразованию.

## Решение
1. Изменена кодировка подключения к MSSQL на `cp1251`
2. Убран CAST в VARCHAR из SQL запроса для поля `start_cost`
3. Форматирование цены теперь происходит на стороне Python, а не SQL

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
