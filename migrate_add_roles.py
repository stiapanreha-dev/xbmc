"""
Скрипт миграции: добавление поля role в таблицу users
Запустите этот скрипт, если база данных уже существует
"""
from app import create_app
from app.models import db, User
from dotenv import load_dotenv

load_dotenv()

app = create_app()

with app.app_context():
    try:
        # Пытаемся добавить столбец role
        with db.engine.begin() as conn:
            conn.execute(db.text('ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT "user"'))
        print("✓ Столбец 'role' успешно добавлен в таблицу users")
    except Exception as e:
        if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
            print("✓ Столбец 'role' уже существует")
        else:
            print(f"Ошибка: {e}")
            exit(1)

    # Назначаем admin роль пользователю admin
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.role = 'admin'
        db.session.commit()
        print(f"✓ Пользователь 'admin' назначен администратором")
    else:
        print("! Пользователь 'admin' не найден")

    print("\nМиграция завершена!")
