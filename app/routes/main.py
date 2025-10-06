from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app.models import db, News, Idea, User
from app.mssql import mssql
from app.decorators import admin_required
from datetime import datetime, timedelta
import io
from openpyxl import Workbook

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Получаем параметры фильтрации
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_text = request.args.get('search_text', '').strip()
    page = int(request.args.get('page', 1))

    # Получаем параметр per_page с валидацией
    per_page_param = request.args.get('per_page', '20')
    try:
        per_page = int(per_page_param)
        if per_page not in [20, 50, 100, 500]:
            per_page = 20
    except ValueError:
        per_page = 20

    # Определяем лимит и доступ на основе авторизации и баланса
    restrict_to_ids = None  # Для ограничения доступа неавторизированных пользователей

    if not current_user.is_authenticated:
        # Без авторизации: только top 50 с пагинацией, email и телефон замаскированы
        max_records = 50
        offset = (page - 1) * per_page
        # Ограничиваем offset в пределах первых 50 записей
        if offset >= max_records:
            offset = 0
            page = 1
        limit = min(per_page, max_records - offset)
        has_full_access = False
        show_masked_email = True
        show_masked_phone = True

        # Получаем ID первых 50 записей для ограничения доступа
        conn = mssql.get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT TOP 50 id
            FROM zakupki
            ORDER BY id DESC
        """)
        top_50_records = cursor.fetchall()
        conn.close()
        restrict_to_ids = [r['id'] for r in top_50_records]

    elif current_user.has_positive_balance() or current_user.is_admin():
        # С положительным балансом или админ: полный доступ, email и телефон открыты
        limit = per_page
        offset = (page - 1) * per_page
        has_full_access = True
        show_masked_email = False
        show_masked_phone = False
    else:
        # С нулевым балансом: полный доступ с пагинацией, но email и телефон замаскированы
        limit = per_page
        offset = (page - 1) * per_page
        has_full_access = True
        show_masked_email = True
        show_masked_phone = True

    # Конвертируем даты
    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d') if date_from else None
    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') if date_to else None

    # Валидация и ограничение периода поиска
    MAX_SEARCH_DAYS = 30

    # Если есть поиск по тексту, но не заданы даты - устанавливаем последние 30 дней
    if search_text and not date_from_obj and not date_to_obj:
        date_to_obj = datetime.now()
        date_from_obj = date_to_obj - timedelta(days=MAX_SEARCH_DAYS)
        date_from = date_from_obj.strftime('%Y-%m-%d')
        date_to = date_to_obj.strftime('%Y-%m-%d')
        flash(f'Поиск выполнен за последние {MAX_SEARCH_DAYS} дней. Для изменения периода укажите даты.', 'info')

    # Если задан только один из диапазона дат при поиске - дополняем вторую дату
    elif search_text:
        if date_from_obj and not date_to_obj:
            date_to_obj = date_from_obj + timedelta(days=MAX_SEARCH_DAYS)
            date_to = date_to_obj.strftime('%Y-%m-%d')
            flash(f'Период поиска ограничен {MAX_SEARCH_DAYS} днями от указанной даты.', 'info')
        elif date_to_obj and not date_from_obj:
            date_from_obj = date_to_obj - timedelta(days=MAX_SEARCH_DAYS)
            date_from = date_from_obj.strftime('%Y-%m-%d')
            flash(f'Период поиска ограничен {MAX_SEARCH_DAYS} днями до указанной даты.', 'info')

    # Ограничение интервала поиска (защита от больших интервалов)
    if search_text and date_from_obj and date_to_obj:
        days_diff = (date_to_obj - date_from_obj).days
        if days_diff > MAX_SEARCH_DAYS:
            # Обрезаем интервал до 30 дней от date_to
            date_from_obj = date_to_obj - timedelta(days=MAX_SEARCH_DAYS)
            date_from = date_from_obj.strftime('%Y-%m-%d')
            flash(f'Интервал поиска ограничен {MAX_SEARCH_DAYS} днями. Период скорректирован.', 'warning')

    # Получаем данные из MSSQL
    result = mssql.get_zakupki(
        date_from=date_from_obj,
        date_to=date_to_obj,
        search_text=search_text if search_text else None,
        limit=limit,
        offset=offset,
        restrict_to_ids=restrict_to_ids,
        count_all=not current_user.is_authenticated  # Для неавторизованных считаем общее количество
    )

    total = result['total']

    return render_template('index.html',
                         zakupki=result['data'],
                         total=total,
                         date_from=date_from or '',
                         date_to=date_to or '',
                         search_text=search_text,
                         has_full_access=has_full_access,
                         show_masked_email=show_masked_email,
                         show_masked_phone=show_masked_phone,
                         page=page,
                         per_page=per_page)

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
    ideas_list = Idea.query.filter_by(status='approved').order_by(Idea.created_at.desc()).all()
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
            user_id=current_user.id if current_user.is_authenticated else None,
            status='pending'
        )
        db.session.add(idea)
        db.session.commit()

        flash('Идея отправлена на модерацию! После проверки администратором она появится на сайте.', 'success')
        return redirect(url_for('main.ideas'))

    return render_template('add_idea.html')

@bp.route('/invite')
def invite():
    return render_template('invite.html')

@bp.route('/support')
def support():
    return render_template('support.html')

@bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@bp.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@bp.route('/offer')
def offer():
    return render_template('offer.html')

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

@bp.route('/admin/ideas')
@admin_required
def admin_ideas():
    # Получаем фильтр по статусу
    status_filter = request.args.get('status', 'pending')

    # Фильтруем идеи
    if status_filter == 'all':
        ideas_list = Idea.query.order_by(Idea.created_at.desc()).all()
    else:
        ideas_list = Idea.query.filter_by(status=status_filter).order_by(Idea.created_at.desc()).all()

    return render_template('admin_ideas.html', ideas_list=ideas_list, status_filter=status_filter)

@bp.route('/admin/ideas/<int:idea_id>/approve', methods=['POST'])
@admin_required
def approve_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    idea.status = 'approved'
    db.session.commit()
    flash(f'Идея "{idea.title}" одобрена', 'success')
    return redirect(url_for('main.admin_ideas'))

@bp.route('/admin/ideas/<int:idea_id>/reject', methods=['POST'])
@admin_required
def reject_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    idea.status = 'rejected'
    db.session.commit()
    flash(f'Идея "{idea.title}" отклонена', 'warning')
    return redirect(url_for('main.admin_ideas'))

@bp.route('/admin/ideas/<int:idea_id>/delete', methods=['POST'])
@admin_required
def delete_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    title = idea.title
    db.session.delete(idea)
    db.session.commit()
    flash(f'Идея "{title}" удалена', 'success')

    # Редирект на страницу, откуда была нажата кнопка удаления
    referer = request.referrer
    if referer and '/ideas' in referer and '/admin/ideas' not in referer:
        return redirect(url_for('main.ideas'))
    return redirect(url_for('main.admin_ideas'))

@bp.route('/admin/news/<int:news_id>/delete', methods=['POST'])
@admin_required
def delete_news(news_id):
    news_item = News.query.get_or_404(news_id)
    title = news_item.title
    db.session.delete(news_item)
    db.session.commit()
    flash(f'Новость "{title}" удалена', 'success')
    return redirect(url_for('main.news'))

@bp.route('/zakupki/<int:zakupki_id>')
@login_required
def zakupki_detail(zakupki_id):
    """Показать детальную информацию о закупке"""
    # Получить параметры фильтрации для возврата к списку
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search_text = request.args.get('search_text', '')
    page = request.args.get('page', '1')
    per_page = request.args.get('per_page', '20')

    # Получить данные закупки
    result = mssql.get_zakupki(limit=1, offset=0, restrict_to_ids=[zakupki_id])

    if not result['data']:
        flash('Закупка не найдена', 'error')
        return redirect(url_for('main.index'))

    zakupka = result['data'][0]

    # Получить спецификации (если есть)
    specifications = mssql.get_specifications(zakupki_id)

    # Определить нужно ли маскировать данные (пользователь уже авторизован благодаря @login_required)
    show_masked_email = False
    show_masked_phone = False

    if not (current_user.has_positive_balance() or current_user.is_admin()):
        show_masked_email = True
        show_masked_phone = True

    return render_template('zakupki_detail.html',
                         zakupka=zakupka,
                         specifications=specifications,
                         show_masked_email=show_masked_email,
                         show_masked_phone=show_masked_phone,
                         date_from=date_from,
                         date_to=date_to,
                         search_text=search_text,
                         page=page,
                         per_page=per_page)

@bp.route('/zakupki/<int:zakupki_id>/specifications')
@login_required
def specifications(zakupki_id):
    """Показать спецификации для закупки (старый роут, редирект на новый)"""
    return redirect(url_for('main.zakupki_detail', zakupki_id=zakupki_id))

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

    # Валидация и ограничение периода поиска (та же логика что и в index)
    MAX_SEARCH_DAYS = 30

    # Если есть поиск по тексту, но не заданы даты - устанавливаем последние 30 дней
    if search_text and not date_from_obj and not date_to_obj:
        date_to_obj = datetime.now()
        date_from_obj = date_to_obj - timedelta(days=MAX_SEARCH_DAYS)

    # Если задан только один из диапазона дат при поиске - дополняем вторую дату
    elif search_text:
        if date_from_obj and not date_to_obj:
            date_to_obj = date_from_obj + timedelta(days=MAX_SEARCH_DAYS)
        elif date_to_obj and not date_from_obj:
            date_from_obj = date_to_obj - timedelta(days=MAX_SEARCH_DAYS)

    # Ограничение интервала поиска (защита от больших интервалов)
    if search_text and date_from_obj and date_to_obj:
        days_diff = (date_to_obj - date_from_obj).days
        if days_diff > MAX_SEARCH_DAYS:
            # Обрезаем интервал до 30 дней от date_to
            date_from_obj = date_to_obj - timedelta(days=MAX_SEARCH_DAYS)

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
        # Используем start_cost_var если есть, иначе числовой start_cost
        price = row.get('start_cost_var') or (str(row['start_cost']) if row.get('start_cost') else '')

        ws.append([
            row['date_request'].strftime('%d.%m.%Y') if row['date_request'] else '',
            row['purchase_object'],
            price,
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

@bp.route('/admin/sql-query', methods=['GET', 'POST'])
@admin_required
def admin_sql_query():
    """Страница для выполнения произвольных SQL запросов (только для админов)"""
    result = None
    query = ""

    if request.method == 'POST':
        query = request.form.get('query', '').strip()

        if not query:
            flash('Введите SQL запрос', 'warning')
        else:
            result = mssql.execute_query(query)

            if result['success']:
                if result['data']:
                    flash(f'Запрос выполнен успешно. Получено строк: {result["rowcount"]}. Время: {result["query_time"]} мс', 'success')
                else:
                    flash(f'Запрос выполнен успешно. Затронуто строк: {result["rowcount"]}. Время: {result["query_time"]} мс', 'success')
            else:
                flash(f'Ошибка выполнения запроса: {result["error"]}', 'danger')

    return render_template('admin_sql_query.html', result=result, query=query)
