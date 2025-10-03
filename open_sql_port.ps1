# Открытие порта 1433 для SQL Server в брандмауэре Windows
# Запускать от имени Администратора

Write-Host "Открываю порт 1433 для SQL Server..." -ForegroundColor Green

# Удаляем старое правило если существует
Remove-NetFirewallRule -DisplayName "SQL Server Port 1433" -ErrorAction SilentlyContinue

# Создаем новое правило для входящих соединений
New-NetFirewallRule -DisplayName "SQL Server Port 1433" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 1433 `
    -Action Allow `
    -Enabled True `
    -Profile Any

Write-Host "Порт 1433 успешно открыт!" -ForegroundColor Green
Write-Host "Теперь можно подключаться к SQL Server извне." -ForegroundColor Cyan
