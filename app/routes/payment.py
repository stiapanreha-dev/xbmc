from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from app.models import db, Transaction
import requests
import os
import uuid
import json

bp = Blueprint('payment', __name__, url_prefix='/payment')

YUKASSA_SHOP_ID = os.getenv('YUKASSA_SHOP_ID')
YUKASSA_SECRET_KEY = os.getenv('YUKASSA_SECRET_KEY')
YUKASSA_API_URL = 'https://api.yookassa.ru/v3/payments'

@bp.route('/create', methods=['POST'])
@login_required
def create_payment():
    amount = request.form.get('amount')

    if not amount or float(amount) <= 0:
        flash('Укажите корректную сумму', 'danger')
        return redirect(url_for('payment.create_payment'))

    # Создаем транзакцию
    transaction = Transaction(
        user_id=current_user.id,
        amount=float(amount),
        status='pending'
    )
    db.session.add(transaction)
    db.session.commit()

    # Проверяем, настроена ли ЮKassa (если нет - используем демо-режим)
    if YUKASSA_SHOP_ID == 'test-shop-id' or not YUKASSA_SHOP_ID:
        # ДЕМО-РЕЖИМ: Сразу пополняем баланс без реальной оплаты
        transaction.status = 'succeeded'
        transaction.payment_id = f"demo_{uuid.uuid4()}"
        current_user.balance += transaction.amount
        db.session.commit()

        flash(f'Баланс успешно пополнен на {amount} ₽ (демо-режим)', 'success')
        return redirect(url_for('payment.payment_success'))

    # Создаем платеж в ЮKassa
    idempotence_key = str(uuid.uuid4())
    payment_data = {
        "amount": {
            "value": f"{float(amount):.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": os.getenv('YUKASSA_RETURN_URL', 'http://localhost:5000/payment/success')
        },
        "capture": True,
        "description": f"Пополнение баланса пользователя {current_user.username}",
        "metadata": {
            "transaction_id": transaction.id,
            "user_id": current_user.id
        }
    }

    try:
        response = requests.post(
            YUKASSA_API_URL,
            json=payment_data,
            auth=(YUKASSA_SHOP_ID, YUKASSA_SECRET_KEY),
            headers={'Idempotence-Key': idempotence_key}
        )

        if response.status_code == 200:
            payment_response = response.json()
            transaction.payment_id = payment_response['id']
            db.session.commit()

            # Редирект на страницу оплаты ЮKassa
            return redirect(payment_response['confirmation']['confirmation_url'])
        else:
            flash('Ошибка создания платежа', 'danger')
            transaction.status = 'canceled'
            db.session.commit()
            return redirect(url_for('main.index'))

    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'danger')
        transaction.status = 'canceled'
        db.session.commit()
        return redirect(url_for('main.index'))


@bp.route('/success')
def payment_success():
    return render_template('payment_success.html')


@bp.route('/webhook', methods=['POST'])
def webhook():
    """Обработка уведомлений от ЮKassa"""
    event = request.json

    if event['event'] == 'payment.succeeded':
        payment_id = event['object']['id']
        transaction = Transaction.query.filter_by(payment_id=payment_id).first()

        if transaction and transaction.status == 'pending':
            transaction.status = 'succeeded'
            user = transaction.user
            user.balance += transaction.amount
            db.session.commit()

    elif event['event'] == 'payment.canceled':
        payment_id = event['object']['id']
        transaction = Transaction.query.filter_by(payment_id=payment_id).first()

        if transaction:
            transaction.status = 'canceled'
            db.session.commit()

    return {'status': 'ok'}
