# app/routers/bookings.py
# Эндпоинты для заявок: создание клиентом, проверка занятости, ручное добавление из админки.

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, Service
from app.ratelimit import limit_booking
from app.security import get_current_admin
from app.telegram import send_telegram_message, format_booking_message

router = APIRouter()


class BookingCreate(BaseModel):
    """Схема данных для создания заявки с сайта (клиент)."""
    client_name: str = Field(..., min_length=2, max_length=128, description="Имя клиента")
    client_phone: str = Field(..., min_length=10, max_length=32, description="Телефон клиента")
    service_id: Optional[int] = Field(None, description="ID услуги (опционально)")
    service_label: Optional[str] = Field(None, max_length=255, description="Название услуги")
    city: str = Field(..., description="Город приёма: korkino/chelyabinsk/tyumen/samara/perm")
    booking_date: str = Field(..., max_length=16, description="Дата в формате ISO: 2026-11-25")
    booking_time: str = Field(..., max_length=8, description="Время: 14:30")
    comment: Optional[str] = Field(None, max_length=1000, description="Комментарий клиента")


class ManualBookingCreate(BaseModel):
    """Запись, которую Ольга создаёт вручную из своего блокнота (только из админки)."""
    client_name: str = Field(..., min_length=2, max_length=128)
    client_phone: str = Field(..., min_length=10, max_length=32)
    city: str = Field(...)
    booking_date: str = Field(..., max_length=16)
    booking_time: str = Field(..., max_length=8)
    service_label: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = Field(None, max_length=1000)


VALID_CITIES = ["korkino", "chelyabinsk", "tyumen", "samara", "perm"]


def _validate_booking_data(city: str, booking_date: str, booking_time: str):
    """Общая валидация города и даты."""
    if city not in VALID_CITIES:
        raise HTTPException(status_code=400, detail=f"Недопустимый город. Допустимые: {VALID_CITIES}")
    try:
        bd = datetime.fromisoformat(booking_date)
        if bd.date() < datetime.now().date():
            raise HTTPException(status_code=400, detail="Дата записи должна быть в будущем")
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используйте ISO: YYYY-MM-DD")


@router.post("/api/bookings", tags=["bookings"], status_code=201)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(limit_booking),  # защита от спама
):
    """
    Создаёт новую заявку на запись и отправляет уведомление в Telegram.
    """
    _validate_booking_data(booking.city, booking.booking_date, booking.booking_time)

    # Если передан service_id, проверяем его существование и замораживаем название
    if booking.service_id:
        service = db.query(Service).filter(Service.id == booking.service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Услуга не найдена")
        if not booking.service_label:
            booking.service_label = f"{service.category.title} - {service.name}"

    db_booking = Booking(
        client_name=booking.client_name,
        client_phone=booking.client_phone,
        service_id=booking.service_id,
        service_label=booking.service_label,
        city=booking.city,
        booking_date=booking.booking_date,
        booking_time=booking.booking_time,
        comment=booking.comment,
        status="new",
        review_requested=False,
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    # Отправляем уведомление в Telegram
    booking_data = {
        "id": db_booking.id,
        "client_name": db_booking.client_name,
        "client_phone": db_booking.client_phone,
        "city": db_booking.city,
        "service_label": db_booking.service_label or "Не указана",
        "booking_date": db_booking.booking_date,
        "booking_time": db_booking.booking_time,
        "comment": db_booking.comment or "Нет",
    }
    telegram_result = send_telegram_message(format_booking_message(booking_data))

    return {
        "id": db_booking.id,
        "status": "created",
        "telegram_sent": telegram_result.get("ok", False),
    }


@router.get("/api/bookings/availability", tags=["bookings"])
def availability(
    date: str,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Возвращает список занятых времён на указанную дату.
    Если передан city — фильтрует по городу.
    Используется фронтом, чтобы показать серым недоступные слоты.
    """
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используйте ISO: YYYY-MM-DD")

    query = db.query(Booking).filter(Booking.booking_date == date)
    if city:
        query = query.filter(Booking.city == city)
    rows = query.all()

    # Отдаём времена только активных статусов (new / confirmed / completed)
    active_statuses = {"new", "confirmed", "completed"}
    times = []
    for r in rows:
        if r.status in active_statuses:
            times.append({
                "time": r.booking_time,
                "city": r.city,
                "service_label": r.service_label,
                "client_name": r.client_name,
                "status": r.status,
            })
    return {"date": date, "busy": times}


@router.post("/api/bookings/manual", tags=["bookings-admin"], status_code=201)
def create_manual_booking(
    payload: ManualBookingCreate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """
    Запись из блокнота Ольги. Создаётся напрямую в статусе 'confirmed'
    и не триггерит rate-limit. Защищено токеном администратора.
    """
    _validate_booking_data(payload.city, payload.booking_date, payload.booking_time)

    db_booking = Booking(
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        service_id=None,
        service_label=payload.service_label,
        city=payload.city,
        booking_date=payload.booking_date,
        booking_time=payload.booking_time,
        comment=payload.comment,
        status="confirmed",
        review_requested=False,
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    # Уведомляем Ольгу, что запись добавлена вручную
    booking_data = {
        "id": db_booking.id,
        "client_name": db_booking.client_name,
        "client_phone": db_booking.client_phone,
        "city": db_booking.city,
        "service_label": db_booking.service_label or "Не указана",
        "booking_date": db_booking.booking_date,
        "booking_time": db_booking.booking_time,
        "comment": (payload.comment or "—") + "\n(запись из блокнота)",
    }
    send_telegram_message(format_booking_message(booking_data))

    return {
        "id": db_booking.id,
        "status": db_booking.status,
        "created": True,
    }