import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/xbmc_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ЮKassa settings
    YUKASSA_SHOP_ID = os.getenv('YUKASSA_SHOP_ID')
    YUKASSA_SECRET_KEY = os.getenv('YUKASSA_SECRET_KEY')
    YUKASSA_RETURN_URL = os.getenv('YUKASSA_RETURN_URL', 'http://localhost:5000/payment/success')
