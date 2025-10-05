# Автоматический деплой обновлений

## Использование

Просто запустите `deploy.bat` двойным кликом или из командной строки:

```cmd
deploy.bat
```

## Что делает скрипт

1. ✅ Проверяет наличие Git
2. ✅ Обновляет код из GitHub (`git pull origin master`)
3. ✅ Перезапускает Flask сервис (FlaskBusinessDB)
4. ✅ Проверяет статус сервиса

## Требования

- Git должен быть установлен
- NSSM должен находиться в `C:\nssm\win64\nssm.exe`
- Проект должен быть в `C:\soft\business.db`
- Сервис должен быть настроен с именем `FlaskBusinessDB`

## Установка Git (если не установлен)

```powershell
winget install --id Git.Git -e
```

## Ручной деплой (без батника)

Если нужно выполнить деплой вручную:

```powershell
# Перейти в директорию
cd C:\soft\business.db

# Обновить код
git pull origin master

# Перезапустить сервис
C:\nssm\win64\nssm.exe restart FlaskBusinessDB

# Проверить статус
C:\nssm\win64\nssm.exe status FlaskBusinessDB
```

## Устранение проблем

### Git не найден
```powershell
winget install --id Git.Git -e
```

### NSSM не найден
Убедитесь, что NSSM установлен в `C:\nssm\win64\nssm.exe`

### Сервис не запускается
```powershell
# Проверить логи
C:\nssm\win64\nssm.exe status FlaskBusinessDB

# Запустить вручную для проверки ошибок
cd C:\soft\business.db
python run.py
```

### Кодировка в консоли неправильная
Батник автоматически устанавливает UTF-8 (`chcp 65001`), но если проблемы остались, выполните вручную:
```cmd
chcp 65001
deploy.bat
```
