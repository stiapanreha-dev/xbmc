# Установка SSL сертификата на Windows 10

Данная инструкция описывает процесс установки SSL сертификата для работы приложения Business database на Windows 10 с использованием Apache или IIS.

## Требования

- Наличие файлов сертификата:
  - `certificate.crt` или `certificate.pem` - сам сертификат
  - `private.key` - приватный ключ
  - `ca_bundle.crt` или `chain.crt` - промежуточные сертификаты (опционально)

## Вариант 1: Использование с Apache (рекомендуется)

### Шаг 1: Установка Apache для Windows

1. Скачайте Apache для Windows с официального сайта:
   - https://www.apachelounge.com/download/
   - Выберите версию с поддержкой SSL (обычно все версии поддерживают)

2. Распакуйте архив в `C:\Apache24`

3. Установите Visual C++ Redistributable (если требуется):
   - Ссылка указана на странице загрузки Apache

### Шаг 2: Размещение файлов сертификата

1. Создайте папку для сертификатов:
   ```
   C:\Apache24\conf\ssl\
   ```

2. Скопируйте файлы сертификата в эту папку:
   - `C:\Apache24\conf\ssl\certificate.crt`
   - `C:\Apache24\conf\ssl\private.key`
   - `C:\Apache24\conf\ssl\ca_bundle.crt` (если есть)

### Шаг 3: Настройка Apache

1. Откройте файл `C:\Apache24\conf\httpd.conf` в текстовом редакторе (от имени администратора)

2. Раскомментируйте (уберите `#` в начале строки) следующие строки:
   ```apache
   LoadModule ssl_module modules/mod_ssl.so
   LoadModule socache_shmcb_module modules/mod_socache_shmcb.so
   Include conf/extra/httpd-ssl.conf
   ```

3. Откройте файл `C:\Apache24\conf\extra\httpd-ssl.conf`

4. Найдите и измените следующие параметры:

   ```apache
   # Порт HTTPS
   Listen 443

   <VirtualHost _default_:443>
       # Имя сервера (ваш домен)
       ServerName yourdomain.com:443
       ServerAdmin admin@yourdomain.com

       # SSL Engine
       SSLEngine on

       # Пути к сертификатам
       SSLCertificateFile "C:/Apache24/conf/ssl/certificate.crt"
       SSLCertificateKeyFile "C:/Apache24/conf/ssl/private.key"
       SSLCertificateChainFile "C:/Apache24/conf/ssl/ca_bundle.crt"

       # Proxy для Flask приложения
       ProxyPreserveHost On
       ProxyPass / http://127.0.0.1:5000/
       ProxyPassReverse / http://127.0.0.1:5000/

       # Логи
       ErrorLog "logs/ssl_error.log"
       CustomLog "logs/ssl_access.log" common
   </VirtualHost>
   ```

5. Для работы прокси раскомментируйте в `httpd.conf`:
   ```apache
   LoadModule proxy_module modules/mod_proxy.so
   LoadModule proxy_http_module modules/mod_proxy_http.so
   ```

### Шаг 4: Запуск Apache как службы

1. Откройте командную строку от имени администратора

2. Перейдите в папку Apache:
   ```cmd
   cd C:\Apache24\bin
   ```

3. Установите Apache как службу:
   ```cmd
   httpd.exe -k install
   ```

4. Запустите службу:
   ```cmd
   httpd.exe -k start
   ```

5. Для автозапуска службы:
   - Нажмите `Win + R`, введите `services.msc`
   - Найдите службу "Apache2.4"
   - ПКМ → Свойства → Тип запуска: "Автоматически"

### Шаг 5: Настройка Flask приложения

Flask приложение должно работать на локальном порту 5000. Apache будет проксировать запросы к нему.

Убедитесь, что в `run.py` указано:
```python
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
```

### Шаг 6: Настройка Windows Firewall

1. Откройте "Брандмауэр Защитника Windows" → "Дополнительные параметры"
2. Создайте правило для входящих подключений:
   - Тип: Для порта
   - Протокол: TCP
   - Порт: 443
   - Разрешить подключение
   - Имя: "Apache HTTPS"

## Вариант 2: Использование с IIS

### Шаг 1: Конвертация сертификата в PFX

1. Если у вас есть `.crt` и `.key` файлы, их нужно объединить в `.pfx`:

2. Скачайте и установите OpenSSL для Windows:
   - https://slproweb.com/products/Win32OpenSSL.html

3. Откройте командную строку и выполните:
   ```cmd
   cd C:\OpenSSL-Win64\bin
   openssl pkcs12 -export -out certificate.pfx -inkey private.key -in certificate.crt -certfile ca_bundle.crt
   ```

4. Введите пароль для PFX файла (запомните его!)

### Шаг 2: Импорт сертификата в Windows

1. Нажмите `Win + R`, введите `mmc`

2. Файл → Добавить или удалить оснастку

3. Выберите "Сертификаты" → Добавить → Учетная запись компьютера → Локальный компьютер

4. Перейдите: Сертификаты (локальный компьютер) → Личные → Сертификаты

5. ПКМ → Все задачи → Импорт

6. Укажите путь к `.pfx` файлу

7. Введите пароль

8. Выберите "Автоматически выбрать хранилище"

### Шаг 3: Установка IIS и компонентов

1. Панель управления → Программы → Включение или отключение компонентов Windows

2. Отметьте:
   - Internet Information Services
   - Web Management Tools → IIS Management Console
   - World Wide Web Services → Application Development Features → CGI
   - World Wide Web Services → Security → Request Filtering

3. Нажмите OK и дождитесь установки

### Шаг 4: Настройка IIS

1. Откройте "Диспетчер служб IIS" (inetmgr)

2. Выберите ваш сервер → Сертификаты сервера

3. Проверьте, что импортированный сертификат отображается

4. Создайте новый сайт:
   - ПКМ на "Сайты" → Добавить веб-сайт
   - Имя сайта: Business Database
   - Физический путь: `C:\inetpub\wwwroot\businessdb`
   - Привязка: https
   - IP-адрес: Все неназначенные
   - Порт: 443
   - Сертификат SSL: выберите импортированный сертификат

5. Установите модуль HttpPlatformHandler для проксирования к Flask:
   - Скачайте: https://www.iis.net/downloads/microsoft/httpplatformhandler
   - Установите

6. Создайте `web.config` в папке сайта:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <configuration>
     <system.webServer>
       <handlers>
         <add name="httpPlatformHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified" />
       </handlers>
       <httpPlatform processPath="C:\Python39\python.exe"
                     arguments="C:\path\to\your\app\run.py"
                     startupTimeLimit="60"
                     startupRetryCount="3"
                     stdoutLogEnabled="true"
                     stdoutLogFile=".\logs\python.log">
         <environmentVariables>
           <environmentVariable name="PORT" value="%HTTP_PLATFORM_PORT%" />
         </environmentVariables>
       </httpPlatform>
     </system.webServer>
   </configuration>
   ```

## Проверка установки

1. Откройте браузер и перейдите по адресу:
   ```
   https://yourdomain.com
   ```
   или
   ```
   https://localhost
   ```

2. Проверьте, что сертификат действителен (значок замка в адресной строке)

3. Проверьте работу приложения

## Автоматический запуск Flask приложения

### Создание службы Windows для Flask

1. Создайте файл `install_service.py`:
   ```python
   import win32serviceutil
   import win32service
   import win32event
   import servicemanager
   import socket
   import sys
   import os

   class FlaskService(win32serviceutil.ServiceFramework):
       _svc_name_ = "BusinessDatabaseService"
       _svc_display_name_ = "Business Database Flask Service"
       _svc_description_ = "Flask application for Business Database"

       def __init__(self, args):
           win32serviceutil.ServiceFramework.__init__(self, args)
           self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
           socket.setdefaulttimeout(60)
           self.is_alive = True

       def SvcStop(self):
           self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
           win32event.SetEvent(self.hWaitStop)
           self.is_alive = False

       def SvcDoRun(self):
           servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                 servicemanager.PYS_SERVICE_STARTED,
                                 (self._svc_name_, ''))
           self.main()

       def main(self):
           os.chdir(r'C:\path\to\your\app')
           from app import create_app
           app = create_app()
           app.run(host='127.0.0.1', port=5000)

   if __name__ == '__main__':
       if len(sys.argv) == 1:
           servicemanager.Initialize()
           servicemanager.PrepareToHostSingle(FlaskService)
           servicemanager.StartServiceCtrlDispatcher()
       else:
           win32serviceutil.HandleCommandLine(FlaskService)
   ```

2. Установите зависимости:
   ```cmd
   pip install pywin32
   ```

3. Установите службу:
   ```cmd
   python install_service.py install
   ```

4. Запустите службу:
   ```cmd
   python install_service.py start
   ```

## Устранение проблем

### Проверка работы сертификата

1. Проверьте срок действия:
   ```cmd
   openssl x509 -in certificate.crt -noout -dates
   ```

2. Проверьте содержимое сертификата:
   ```cmd
   openssl x509 -in certificate.crt -noout -text
   ```

### Ошибки Apache

1. Проверьте логи:
   - `C:\Apache24\logs\error.log`
   - `C:\Apache24\logs\ssl_error.log`

2. Проверьте конфигурацию:
   ```cmd
   C:\Apache24\bin\httpd.exe -t
   ```

### Ошибки прав доступа

1. Убедитесь, что файлы сертификата доступны для чтения

2. Для IIS убедитесь, что пользователь IIS_IUSRS имеет права на чтение приватного ключа:
   - ПКМ на файл → Свойства → Безопасность
   - Добавьте пользователя IIS_IUSRS с правами чтения

## Дополнительные рекомендации

1. **Перенаправление HTTP на HTTPS**:
   В Apache добавьте в `httpd.conf`:
   ```apache
   <VirtualHost *:80>
       ServerName yourdomain.com
       Redirect permanent / https://yourdomain.com/
   </VirtualHost>
   ```

2. **Усиление безопасности SSL** (опционально):
   В `httpd-ssl.conf`:
   ```apache
   SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
   SSLCipherSuite HIGH:!aNULL:!MD5:!3DES
   SSLHonorCipherOrder on
   ```

3. **Автообновление сертификата**:
   - Настройте задачу в планировщике Windows для автоматического обновления сертификата
   - Используйте Certbot для Let's Encrypt (если применимо)

## Поддержка

Если возникли проблемы с установкой, проверьте:
- Логи Apache/IIS
- Права доступа к файлам сертификата
- Настройки брандмауэра Windows
- Правильность путей в конфигурационных файлах
