"""
Сервис для отправки SMS через SMS.ru API
"""
import os
import requests


class SMSService:
    def __init__(self):
        self.api_key = os.getenv('SMSRU_API_KEY', '')
        self.api_url = 'https://sms.ru/sms/send'
        self.from_name = os.getenv('SMSRU_FROM_NAME', '')  # Буквенный отправитель (опционально)

    def send_sms(self, phone, text):
        """
        Отправка SMS через SMS.ru API

        Args:
            phone (str): Номер телефона в международном формате (например, 79213771213)
            text (str): Текст сообщения

        Returns:
            bool: True если отправка успешна, False если ошибка
        """
        if not self.api_key:
            print("SMSRU_API_KEY не настроен в .env")
            return False

        # Убираем все символы кроме цифр
        phone_clean = ''.join(filter(str.isdigit, phone))

        # Если номер начинается с 8, заменяем на 7
        if phone_clean.startswith('8'):
            phone_clean = '7' + phone_clean[1:]

        # Если номер не начинается с 7, добавляем 7
        if not phone_clean.startswith('7'):
            phone_clean = '7' + phone_clean

        try:
            params = {
                'api_id': self.api_key,
                'to': phone_clean,
                'msg': text,
                'json': 1  # Получаем ответ в JSON
            }

            # Если настроен буквенный отправитель
            if self.from_name:
                params['from'] = self.from_name

            response = requests.get(self.api_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Проверяем статус в ответе
                if data.get('status') == 'OK':
                    print(f"SMS отправлено успешно на {phone_clean}")
                    return True
                else:
                    error_code = data.get('status_code', 'unknown')
                    error_text = data.get('status_text', 'неизвестная ошибка')
                    print(f"Ошибка SMS.ru: {error_code} - {error_text}")
                    return False
            else:
                print(f"HTTP ошибка: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса к SMS.ru: {e}")
            return False
        except Exception as e:
            print(f"Неожиданная ошибка при отправке SMS: {e}")
            return False

    def send_verification_code(self, phone, code):
        """
        Отправка кода верификации на телефон

        Args:
            phone (str): Номер телефона
            code (str): Код верификации

        Returns:
            bool: True если отправка успешна
        """
        text = f"Ваш код подтверждения Business database: {code}\n\nКод действителен 10 минут."
        return self.send_sms(phone, text)


# Singleton instance
sms_service = SMSService()
