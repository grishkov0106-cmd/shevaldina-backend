# app/telegram.py
# Отправка уведомлений в Telegram через Bot API

import requests
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(text: str) -> dict:
    """
    Отправляет текст в Telegram-чат.
    Возвращает ответ от API (success или error).
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {"ok": False, "error": "Telegram credentials not configured"}
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        return data
    except Exception as e:
        return {"ok": False, "error": str(e)}


def format_booking_message(booking: dict) -> str:
    """Форматирует заявку в красивое сообщение для Telegram."""
    return (
        f"🔔 <b>Новая заявка на запись!</b>\n\n"
        f"👤 <b>Клиент:</b> {booking['client_name']}\n"
        f"📞 <b>Телефон:</b> {booking['client_phone']}\n"
        f"🏙 <b>Город:</b> {booking['city']}\n"
        f"💆 <b>Услуга:</b> {booking.get('service_label', 'Не указана')}\n"
        f"📅 <b>Дата:</b> {booking['booking_date']}\n"
        f"⏰ <b>Время:</b> {booking['booking_time']}\n"
        f"💬 <b>Комментарий:</b> {booking.get('comment', 'Нет')}\n\n"
        f"🆔 ID заявки: {booking.get('id', 'N/A')}"
    )