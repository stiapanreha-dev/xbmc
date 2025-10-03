from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app.models import db, News, Idea, User
from app.mssql import mssql
from app.decorators import admin_required
from datetime import datetime
import io
from openpyxl import Workbook

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    # Получаем параметры фильтрации
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_text = request.args.get('search_text', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 100

    # Конвертируем даты
    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d') if date_from else None
    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') if date_to else None

    # Получаем данные из MSSQL
    result = mssql.get_zakupki(
        date_from=date_from_obj,
        date_to=date_to_obj,
        search_text=search_text if search_text else None,
        limit=per_page,
        offset=(page - 1) * per_page
    )

    return render_template('index.html',
                         zakupki=result['data'],
                         total=result['total'],
                         date_from=date_from or '',
                         date_to=date_to or '',
                         search_text=search_text)

@bp.route('/news')
def news():
    news_list = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).all()
    return render_template('news.html', news_list=news_list)

@bp.route('/news/add', methods=['GET', 'POST'])
@admin_required
def add_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            flash('Заполните все поля', 'danger')
            return redirect(url_for('main.add_news'))

        news_item = News(
            title=title,
            content=content,
            is_published=True
        )
        db.session.add(news_item)
        db.session.commit()

        flash('Новость успешно добавлена!', 'success')
        return redirect(url_for('main.news'))

    return render_template('add_news.html')

@bp.route('/ideas')
def ideas():
    ideas_list = Idea.query.order_by(Idea.created_at.desc()).all()
    return render_template('ideas.html', ideas_list=ideas_list)

@bp.route('/ideas/add', methods=['GET', 'POST'])
def add_idea():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if not title or not description:
            flash('Заполните все поля', 'danger')
            return redirect(url_for('main.add_idea'))

        idea = Idea(
            title=title,
            description=description,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(idea)
        db.session.commit()

        flash('Идея успешно добавлена!', 'success')
        return redirect(url_for('main.ideas'))

    return render_template('add_idea.html')

@bp.route('/invite')
def invite():
    return render_template('invite.html')

@bp.route('/support')
def support():
    return render_template('support.html')

@bp.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@bp.route('/admin/users/<int:user_id>/toggle_admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)

    # Запретить изменение собственной роли
    if user.id == current_user.id:
        flash('Вы не можете изменить свою собственную роль', 'danger')
        return redirect(url_for('main.admin_users'))

    if user.role == 'admin':
        user.role = 'user'
        flash(f'Права администратора у {user.username} отозваны', 'success')
    else:
        user.role = 'admin'
        flash(f'{user.username} назначен администратором', 'success')

    db.session.commit()
    return redirect(url_for('main.admin_users'))

@bp.route('/export')
@login_required
def export_zakupki():
    # Получаем параметры фильтрации
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_text = request.args.get('search_text', '').strip()

    # Конвертируем даты
    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d') if date_from else None
    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') if date_to else None

    # Получаем все данные (без лимита)
    result = mssql.get_zakupki(
        date_from=date_from_obj,
        date_to=date_to_obj,
        search_text=search_text if search_text else None,
        limit=10000,
        offset=0
    )

    # Создаем Excel файл
    wb = Workbook()
    ws = wb.active
    ws.title = "Закупки"

    # Заголовки
    headers = ['Дата запроса', 'Товар/услуга', 'Цена контракта', 'Покупатель', 'Email', 'Телефон', 'Адрес']
    ws.append(headers)

    # Данные
    for row in result['data']:
        ws.append([
            row['date_request'].strftime('%d.%m.%Y') if row['date_request'] else '',
            row['purchase_object'],
            str(row['start_cost']) if row['start_cost'] else '',
            row['customer'],
            row['email'],
            row['phone'],
            row['address']
        ])

    # Сохраняем в память
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'zakupki_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )
