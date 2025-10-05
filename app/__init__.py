from flask import Flask
from flask_login import LoginManager
from app.models import db, User
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

login_manager = LoginManager()

def create_app():
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///xbmc.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_AS_ASCII'] = False  # Поддержка Unicode в JSON

    # Настройка кодировки для ответов
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context processor для счетчиков в навбаре
    @app.context_processor
    def inject_counters():
        from app.models import News, Idea
        from app.utils import mask_email, mask_phone, format_price
        from app.mssql import mssql
        return {
            'news_count': News.query.filter_by(is_published=True).count(),
            'ideas_count': Idea.query.filter_by(status='approved').count(),
            'mask_email': mask_email,
            'mask_phone': mask_phone,
            'format_price': format_price,
            'mssql_stats': mssql.query_stats
        }

    from app.routes import main, auth, payment
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(payment.bp)

    # Добавляем middleware для установки правильной кодировки в заголовках
    @app.after_request
    def after_request(response):
        response.headers['Content-Type'] = response.headers.get('Content-Type', 'text/html; charset=utf-8')
        if 'charset' not in response.headers.get('Content-Type', ''):
            response.headers['Content-Type'] += '; charset=utf-8'
        return response

    return app
