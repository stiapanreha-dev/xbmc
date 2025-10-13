"""
Вспомогательные функции
"""

def mask_email(email, mask_percentage=45):
    """
    Маскирует email на заданный процент (по умолчанию 45%)
    Если вместо email передан телефон - маскирует как телефон

    Примеры:
    test@example.com → te**@ex****e.com
    long.email@domain.com → lon****il@do***n.com
    +79161234567 → +7916*****67 (автоматически распознает телефон)
    """
    if not email:
        return email

    # Если это не email (нет @), проверяем, не телефон ли это
    if '@' not in email:
        # Проверяем, похоже ли на телефон (содержит в основном цифры)
        digits = ''.join(c for c in str(email) if c.isdigit())
        if len(digits) >= 7:  # Минимум 7 цифр для телефона
            return mask_phone(email)
        return email

    local, domain = email.split('@')
    domain_name, domain_ext = domain.rsplit('.', 1) if '.' in domain else (domain, '')

    # Маскируем локальную часть
    local_visible = max(2, int(len(local) * (1 - mask_percentage / 100)))
    local_masked = local[:local_visible] + '*' * (len(local) - local_visible)

    # Маскируем доменное имя
    domain_visible = max(2, int(len(domain_name) * (1 - mask_percentage / 100)))
    domain_masked = domain_name[:domain_visible] + '*' * (len(domain_name) - domain_visible)

    # Собираем обратно
    if domain_ext:
        # Показываем первую букву расширения
        domain_ext_masked = domain_ext[0] + '*' * (len(domain_ext) - 1) if len(domain_ext) > 1 else domain_ext
        return f"{local_masked}@{domain_masked}.{domain_ext_masked}"
    else:
        return f"{local_masked}@{domain_masked}"


def mask_phone(phone, mask_percentage=50):
    """
    Маскирует телефон на заданный процент (по умолчанию 50%)

    Примеры:
    +79161234567 → +7916*****67
    89161234567 → 8916****567
    """
    if not phone:
        return phone

    # Удаляем все кроме цифр и +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

    visible_start = 4  # Показываем первые 4 символа
    visible_end = 2    # Показываем последние 2

    if len(cleaned) <= visible_start + visible_end:
        return phone

    middle_length = len(cleaned) - visible_start - visible_end

    return cleaned[:visible_start] + '*' * middle_length + cleaned[-visible_end:]


def mask_site(site, mask_percentage=45):
    """
    Маскирует сайт на заданный процент (по умолчанию 45%)

    Примеры:
    example.com → exa***e.com
    www.site-name.ru → www.sit*****e.ru
    subdomain.example.com → sub***ain.exa***e.com
    """
    if not site:
        return site

    # Убираем протокол если есть
    site_clean = site.replace('http://', '').replace('https://', '').strip('/')

    # Разделяем на части по точкам
    parts = site_clean.split('.')

    if len(parts) < 2:
        # Если нет точек, просто маскируем часть строки
        visible = max(3, int(len(site_clean) * (1 - mask_percentage / 100)))
        return site_clean[:visible] + '*' * (len(site_clean) - visible)

    # Маскируем каждую часть (кроме последней - расширения)
    masked_parts = []
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            # Последняя часть (расширение) - показываем первую букву
            if len(part) > 1:
                masked_parts.append(part[0] + '*' * (len(part) - 1))
            else:
                masked_parts.append(part)
        else:
            # Остальные части маскируем
            visible = max(3, int(len(part) * (1 - mask_percentage / 100)))
            masked_parts.append(part[:visible] + '*' * (len(part) - visible))

    return '.'.join(masked_parts)


def format_price(value):
    """Безопасное форматирование цены"""
    if not value:
        return '-'

    # Если это уже число
    if isinstance(value, (int, float)):
        return f"{value:,.2f} ₽"

    # Если это строка
    if isinstance(value, str):
        # Убираем пробелы и проверяем, является ли это числом
        value_stripped = value.strip()

        # Проверяем, содержит ли строка только цифры, точку или запятую
        clean_str = value_stripped.replace(',', '').replace('.', '').replace(' ', '').replace('-', '')

        if not clean_str.isdigit():
            # Не число - возвращаем как есть
            return value

        # Пытаемся преобразовать в число
        try:
            num = float(value_stripped.replace(',', '').replace(' ', ''))
            return f"{num:,.2f} ₽"
        except (ValueError, AttributeError):
            return value

    return str(value)
