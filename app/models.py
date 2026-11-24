from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, func
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """Админы (Ольга и, возможно, редакторы)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), default="admin", nullable=False)  # admin | editor
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Category(Base):
    """Направления прайса: SMAS, инъекции, обучение и т.д."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, nullable=False, index=True)  # "smas"
    title = Column(String(128), nullable=False)                          # "SMAS-лифтинг"
    sort_order = Column(Integer, default=0, nullable=False)

    services = relationship("Service", back_populates="category")


class Service(Base):
    """Конкретная процедура с ценой и списком городов."""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    price = Column(String(64), nullable=False)   # строкой: "20 000" / "Индивидуально" / диапазон
    unit = Column(String(64), nullable=True)     # "сеанс", "за шт"
    note = Column(Text, nullable=True)           # комментарий
    # cities храним как JSON-строку: '["korkino","chelyabinsk"]' или '["all"]'
    cities = Column(String(512), default='["all"]', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    category = relationship("Category", back_populates="services")


class Booking(Base):
    """Заявка клиента на запись."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(128), nullable=False)
    client_phone = Column(String(32), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    service_label = Column(String(255), nullable=True)  # заморозка названия на момент заявки
    city = Column(String(32), nullable=False, index=True)  # korkino/chelyabinsk/...
    booking_date = Column(String(16), nullable=False)      # ISO "2026-11-20"
    booking_time = Column(String(8), nullable=False)       # "14:30"
    status = Column(String(16), default="new", nullable=False, index=True)
    # new | confirmed | completed | cancelled
    comment = Column(Text, nullable=True)
    review_requested = Column(Boolean, default=False, nullable=False)  # слали ли ссылку на отзыв
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Review(Base):
    """Отзыв клиента. Проходит модерацию перед публикацией."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    author_name = Column(String(128), nullable=False)
    author_city = Column(String(64), nullable=True)
    text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1..5, опционально
    status = Column(String(16), default="pending", nullable=False, index=True)
    # pending | published | rejected
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)  # связь с визитом
    created_at = Column(DateTime, server_default=func.now())