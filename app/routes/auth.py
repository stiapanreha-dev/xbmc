from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, EmailVerification
from app.email_service import email_service
from app.sms_service import sms_service
from datetime import datetime, timedelta

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone', '').strip()  # Телефон опционален

        if not username or not email:
            flash('Заполните обязательные поля (имя и email)', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'danger')
            return redirect(url_for('auth.register'))

        # Генерируем сильный пароль
        password = email_service.generate_password()

        # Создаем пользователя (неверифицированный)
        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Получаем ID пользователя без commit

        # Генерируем код верификации email
        code = EmailVerification.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        verification = EmailVerification(
            user_id=user.id,
            code=code,
            verification_type='email',
            expires_at=expires_at
        )
        db.session.add(verification)
        db.session.commit()  # Сохраняем все вместе

        # Отправляем email с кодом и паролем
        verification_sent = email_service.send_verification_code(email, code)
        password_sent = email_service.send_password_email(email, username, password)

        if verification_sent and password_sent:
            # Сохраняем user_id в сессии для подтверждения
            session['pending_user_id'] = user.id
            flash('Регистрация успешна! Проверьте email - мы отправили вам код подтверждения и пароль для входа.', 'success')
            return redirect(url_for('auth.verify_email'))
        else:
            flash('Ошибка отправки email. Попробуйте позже.', 'danger')
            # Откатываем транзакцию если не удалось отправить email
            db.session.rollback()
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Проверяем верификацию email
            if not user.email_verified:
                flash('Пожалуйста, подтвердите ваш email перед входом.', 'warning')
                # Сохраняем user_id в сессии для повторной верификации
                session['pending_user_id'] = user.id
                return redirect(url_for('auth.verify_email'))

            login_user(user)
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')

@bp.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    # Проверяем, есть ли pending_user_id в сессии
    user_id = session.get('pending_user_id')
    if not user_id:
        flash('Сессия истекла. Зарегистрируйтесь заново.', 'warning')
        return redirect(url_for('auth.register'))

    user = User.query.get(user_id)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        if not code or len(code) != 6:
            flash('Введите 6-значный код', 'danger')
            return redirect(url_for('auth.verify_email'))

        # Ищем последний неиспользованный код
        verification = EmailVerification.query.filter_by(
            user_id=user.id,
            verification_type='email',
            is_used=False
        ).order_by(EmailVerification.created_at.desc()).first()

        if not verification:
            flash('Код верификации не найден. Запросите новый код.', 'danger')
            return redirect(url_for('auth.verify_email'))

        if verification.is_valid(code):
            # Код правильный!
            user.email_verified = True
            user.phone_verified = True  # Автоматически подтверждаем телефон
            verification.is_used = True
            db.session.commit()

            # Очищаем сессию и логиним пользователя
            session.pop('pending_user_id', None)
            login_user(user)
            flash('Email успешно подтвержден! Добро пожаловать!', 'success')
            return redirect(url_for('main.index'))
        else:
            if verification.is_expired():
                flash('Код истек. Запросите новый код.', 'warning')
            else:
                flash('Неверный код. Проверьте и попробуйте снова.', 'danger')

    return render_template('verify_email.html')

@bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    user_id = session.get('pending_user_id')
    if not user_id:
        flash('Сессия истекла.', 'warning')
        return redirect(url_for('auth.register'))

    user = User.query.get(user_id)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('auth.register'))

    # Помечаем старые коды как использованные
    old_verifications = EmailVerification.query.filter_by(
        user_id=user.id,
        verification_type='email',
        is_used=False
    ).all()
    for v in old_verifications:
        v.is_used = True

    # Генерируем новый код
    code = EmailVerification.generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    verification = EmailVerification(
        user_id=user.id,
        code=code,
        verification_type='email',
        expires_at=expires_at
    )
    db.session.add(verification)
    db.session.commit()

    # Отправляем email
    if email_service.send_verification_code(user.email, code):
        flash('Новый код отправлен на ваш email', 'success')
    else:
        flash('Ошибка отправки email', 'danger')

    return redirect(url_for('auth.verify_email'))

@bp.route('/verify_phone', methods=['GET', 'POST'])
def verify_phone():
    # Проверяем, есть ли pending_user_id в сессии
    user_id = session.get('pending_user_id')
    if not user_id:
        flash('Сессия истекла. Зарегистрируйтесь заново.', 'warning')
        return redirect(url_for('auth.register'))

    user = User.query.get(user_id)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('auth.register'))

    # Проверяем, подтвержден ли email
    if not user.email_verified:
        flash('Сначала подтвердите email', 'warning')
        return redirect(url_for('auth.verify_email'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        if not code or len(code) != 6:
            flash('Введите 6-значный код', 'danger')
            return redirect(url_for('auth.verify_phone'))

        # Ищем последний неиспользованный код для телефона
        verification = EmailVerification.query.filter_by(
            user_id=user.id,
            verification_type='phone',
            is_used=False
        ).order_by(EmailVerification.created_at.desc()).first()

        if not verification:
            flash('Код верификации не найден. Запросите новый код.', 'danger')
            return redirect(url_for('auth.verify_phone'))

        if verification.is_valid(code):
            # Код правильный!
            user.phone_verified = True
            verification.is_used = True
            db.session.commit()

            # Удаляем из сессии
            session.pop('pending_user_id', None)

            flash('Телефон успешно подтвержден! Теперь вы можете войти.', 'success')
            return redirect(url_for('auth.login'))
        else:
            if verification.is_expired():
                flash('Код истек. Запросите новый код.', 'warning')
            else:
                flash('Неверный код. Проверьте и попробуйте снова.', 'danger')

    else:
        # GET запрос - отправляем SMS код при первом заходе
        # Проверяем, нужно ли отправлять новый код
        last_verification = EmailVerification.query.filter_by(
            user_id=user.id,
            verification_type='phone',
            is_used=False
        ).order_by(EmailVerification.created_at.desc()).first()

        # Отправляем код только если нет активного кода или он истек
        if not last_verification or last_verification.is_expired():
            # Генерируем код верификации телефона
            code = EmailVerification.generate_code()
            expires_at = datetime.utcnow() + timedelta(minutes=10)

            verification = EmailVerification(
                user_id=user.id,
                code=code,
                verification_type='phone',
                expires_at=expires_at
            )
            db.session.add(verification)
            db.session.commit()

            # Отправляем SMS с кодом
            if not sms_service.send_verification_code(user.phone, code):
                flash('Ошибка отправки SMS. Попробуйте позже.', 'danger')

    return render_template('verify_phone.html', phone=user.phone)

@bp.route('/resend_phone_verification', methods=['POST'])
def resend_phone_verification():
    user_id = session.get('pending_user_id')
    if not user_id:
        flash('Сессия истекла.', 'warning')
        return redirect(url_for('auth.register'))

    user = User.query.get(user_id)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('auth.register'))

    # Помечаем старые коды как использованные
    old_verifications = EmailVerification.query.filter_by(
        user_id=user.id,
        verification_type='phone',
        is_used=False
    ).all()
    for v in old_verifications:
        v.is_used = True

    # Генерируем новый код
    code = EmailVerification.generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    verification = EmailVerification(
        user_id=user.id,
        code=code,
        verification_type='phone',
        expires_at=expires_at
    )
    db.session.add(verification)
    db.session.commit()

    # Отправляем SMS
    if sms_service.send_verification_code(user.phone, code):
        flash('Новый код отправлен на ваш телефон', 'success')
    else:
        flash('Ошибка отправки SMS', 'danger')

    return redirect(url_for('auth.verify_phone'))

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))
