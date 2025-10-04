#!/usr/bin/env python3
"""
Database initialization script
Run from project root: python3 scripts/init_db.py
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, News
from dotenv import load_dotenv

load_dotenv()

app = create_app()

with app.app_context():
    # Создаем таблицы
    db.create_all()
    print("База данных инициализирована!")

    # Создаем тестового пользователя-администратора
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            phone='+79213771213',
            balance=287.00,
            role='admin',
            email_verified=True,
            phone_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    else:
        # Обновляем роль и верификацию если пользователь уже существует
        admin.role = 'admin'
        admin.email_verified = True
        admin.phone_verified = True
        if not admin.phone:
            admin.phone = '+79213771213'

    # Создаем тестовую новость
    if not News.query.first():
        news = News(
            title='Добро пожаловать!',
            content='Добро пожаловать на наш сайт! Здесь вы можете пополнить баланс и управлять своим аккаунтом.'
        )
        db.session.add(news)

    db.session.commit()
    print("Тестовые данные добавлены!")
    print("Логин: admin")
    print("Пароль: admin123")
