# app/routers/admin.py
"""
Админ-панель: HTML-страница + защищённые API.
Заявки, прайс (категории/услуги), статистика, порядок отображения.
Схема читается через инспекцию моделей — работает с текущей models.py.
"""

from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import (
    Column, Integer, String, UniqueConstraint, Float, Numeric,
    JSON as SA_JSON, inspect as sa_inspect,
)
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app import models as _m
from app.security import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])

Booking = _m.Booking
Service = _m.Service
Category = getattr(_m, "Category", None)
if Category is None:
    _rel = sa_inspect(Service).relationships.get("category")
    Category = _rel.mapper.class_ if _rel is not None else None

ADMIN_HTML_PATH = Path(__file__).parent.parent / "static" / "admin.html"

CITIES = [
    {"id": "korkino", "title": "Коркино"},
    {"id": "chelyabinsk", "title": "Челябинск"},
    {"id": "tyumen", "title": "Тюмень"},
    {"id": "samara", "title": "Самара"},
    {"id": "perm", "title": "Пермь"},
    {"id": "all", "title": "Все города"},
]
CITY_TITLES = {c["id"]: c["title"] for c in CITIES}
STATUSES = ["new", "confirmed", "completed", "cancelled"]


class AdminOrder(Base):
    """Порядок отображения услуг, задаваемый перетаскиванием."""
    __tablename__ = "admin_display_order"
    id = Column(Integer, primary_key=True)
    entity = Column(String(32), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    __table_args__ = (UniqueConstraint("entity", "entity_id", name="uq_admin_order_entity"),)


# ---------- инспекция схемы ----------

def _keys(model) -> list:
    if model is None:
        return []
    return [c.key for c in sa_inspect(model).mapper.column_attrs]


def _pick(model, candidates, default=None):
    ks = _keys(model)
    for c in candidates:
        if c in ks:
            return c
    return default


CAT_KEY = _pick(Category, ("key", "slug", "code", "cat", "cat_key", "ident"))
CAT_TITLE = _pick(Category, ("title", "name", "label"))
SVC_PRICE = _pick(Service, ("price", "cost", "price_from"), "price")
SVC_CITIES = _pick(Service, ("cities", "city_list", "city"))
SVC_DESC = _pick(Service, ("description", "desc", "details", "note", "info"))
SVC_ACTIVE = _pick(Service, ("is_active", "active", "enabled", "visible"))


def _caps() -> dict:
    return {
        "service_description": bool(SVC_DESC),
        "service_active": bool(SVC_ACTIVE),
        "service_cities": bool(SVC_CITIES),
        "categories": Category is not None,
    }


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = "".join(ch for ch in str(v) if ch.isdigit() or ch in ".,")
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _cities_list(raw) -> list:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw]
    s = str(raw).strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            v = json.loads(s)
            return [str(x) for x in v] if isinstance(v, list) else []
        except Exception:
            pass
    return [p.strip() for p in s.replace(";", ",").split(",") if p.strip()]


def _cities_store(values: list):
    col = sa_inspect(Service).columns.get(SVC_CITIES) if SVC_CITIES else None
    if col is not None and isinstance(col.type, SA_JSON):
        return values
    return ",".join(values)


def _price_store(v):
    col = sa_inspect(Service).columns.get(SVC_PRICE)
    if col is not None and isinstance(col.type, (Integer, Float, Numeric)):
        n = _num(v)
        if n is None:
            return None
        return int(n) if isinstance(col.type, Integer) else n
    return str(v)


# ---------- сериализация ----------

def _cat_out(c, counts=None):
    return {
        "id": c.id,
        "key": getattr(c, CAT_KEY) if CAT_KEY else str(c.id),
        "title": getattr(c, CAT_TITLE) if CAT_TITLE else f"Категория {c.id}",
        "count": (counts or {}).get(c.id, 0),
    }


def _svc_out(s, cats):
    c = cats.get(s.category_id)
    raw = getattr(s, SVC_PRICE, None)
    return {
        "id": s.id,
        "name": getattr(s, "name", ""),
        "category_id": s.category_id,
        "cat_key": c["key"] if c else "",
        "cat_title": c["title"] if c else "Без категории",
        "price": raw,
        "price_num": _num(raw),
        "cities": _cities_list(getattr(s, SVC_CITIES, None)) if SVC_CITIES else [],
        "description": getattr(s, SVC_DESC, None) if SVC_DESC else None,
        "is_active": bool(getattr(s, SVC_ACTIVE, True)) if SVC_ACTIVE else True,
    }


def _book_out(b, price_map=None):
    ca = getattr(b, "created_at", None)
    return {
        "id": b.id,
        "client_name": b.client_name,
        "client_phone": b.client_phone,
        "city": b.city,
        "city_title": CITY_TITLES.get(b.city, b.city),
        "service_id": getattr(b, "service_id", None),
        "service_label": getattr(b, "service_label", None),
        "booking_date": b.booking_date,
        "booking_time": b.booking_time,
        "comment": getattr(b, "comment", None),
        "status": b.status,
        "price_num": (price_map or {}).get(getattr(b, "service_id", None)),
        "created_at": ca.isoformat() if ca else None,
    }


def _order_map(db: Session, entity: str) -> dict:
    rows = db.query(AdminOrder).filter(AdminOrder.entity == entity).all()
    return {r.entity_id: r.position for r in rows}


def _sorted(items, omap: dict):
    return sorted(items, key=lambda x: (0, omap[x.id]) if x.id in omap else (1, x.id))


# ---------- схемы запросов ----------

class BookingStatusIn(BaseModel):
    status: str


class BookingRestoreIn(BaseModel):
    id: Optional[int] = None
    client_name: str
    client_phone: str
    city: str
    service_id: Optional[int] = None
    service_label: Optional[str] = None
    booking_date: str
    booking_time: str
    comment: Optional[str] = None
    status: str = "new"


class ServiceIn(BaseModel):
    id: Optional[int] = None
    name: str
    category_id: int
    price: Optional[str] = None
    cities: list = []
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ServicePatchIn(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[str] = None
    cities: Optional[list] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ReorderIn(BaseModel):
    ids: list


# ---------- страница и мета ----------

@router.get("", response_class=HTMLResponse)
def admin_page():
    if not ADMIN_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="admin.html не найден")
    return ADMIN_HTML_PATH.read_text(encoding="utf-8")


@router.get("/meta")
def meta(admin: str = Depends(get_current_admin)):
    return {"capabilities": _caps(), "cities": CITIES, "statuses": STATUSES}


# ---------- статистика ----------

@router.get("/stats")
def stats(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    bookings = db.query(Booking).all()
    services = db.query(Service).all()
    cats = db.query(Category).all() if Category is not None else []

    price_map = {s.id: (_num(getattr(s, SVC_PRICE, None)) or 0) for s in services}
    by_status = {s: 0 for s in STATUSES}
    by_city, today = {}, date.today()
    upcoming, revenue = 0, 0.0
    series = {(today - timedelta(days=i)).isoformat(): 0 for i in range(13, -1, -1)}

    for b in bookings:
        by_status[b.status] = by_status.get(b.status, 0) + 1
        by_city[b.city] = by_city.get(b.city, 0) + 1
        try:
            bd = datetime.fromisoformat(b.booking_date).date()
            if bd >= today and b.status in ("new", "confirmed"):
                upcoming += 1
        except Exception:
            pass
        if b.status in ("confirmed", "completed"):
            revenue += price_map.get(getattr(b, "service_id", None), 0) or 0
        ca = getattr(b, "created_at", None)
        if ca:
            k = ca.date().isoformat()
            if k in series:
                series[k] += 1

    active = sum(1 for s in services if bool(getattr(s, SVC_ACTIVE, True))) if SVC_ACTIVE else len(services)

    return {
        "total_bookings": len(bookings),
        "by_status": by_status,
        "by_city": [{"city": k, "title": CITY_TITLES.get(k, k), "count": v}
                    for k, v in sorted(by_city.items(), key=lambda x: -x[1])],
        "upcoming": upcoming,
        "revenue": revenue,
        "services_total": len(services),
        "services_active": active,
        "categories_total": len(cats),
        "series": [{"date": k, "count": v} for k, v in series.items()],
    }


# ---------- заявки ----------

@router.get("/bookings")
def list_bookings(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    price_map = {s.id: _num(getattr(s, SVC_PRICE, None)) for s in db.query(Service).all()}
    rows = db.query(Booking).all()
    rows.sort(key=lambda b: (getattr(b, "created_at", None) or datetime.min, b.id), reverse=True)
    return [_book_out(b, price_map) for b in rows]


@router.post("/bookings", status_code=201)
def restore_booking(payload: BookingRestoreIn, db: Session = Depends(get_db),
                    admin: str = Depends(get_current_admin)):
    if payload.status not in STATUSES:
        raise HTTPException(status_code=400, detail="Недопустимый статус")
    b = Booking(
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        city=payload.city,
        service_id=payload.service_id,
        service_label=payload.service_label,
        booking_date=payload.booking_date,
        booking_time=payload.booking_time,
        comment=payload.comment,
        status=payload.status,
    )
    if hasattr(Booking, "review_requested"):
        b.review_requested = False
    if payload.id is not None:
        b.id = payload.id
    db.add(b)
    db.commit()
    db.refresh(b)
    return _book_out(b)


@router.patch("/bookings/{booking_id}")
def patch_booking(booking_id: int, payload: BookingStatusIn,
                  db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    if payload.status not in STATUSES:
        raise HTTPException(status_code=400, detail=f"Допустимые статусы: {STATUSES}")
    b = db.query(Booking).filter(Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    b.status = payload.status
    db.commit()
    db.refresh(b)
    return _book_out(b)


@router.delete("/bookings/{booking_id}")
def remove_booking(booking_id: int, db: Session = Depends(get_db),
                   admin: str = Depends(get_current_admin)):
    b = db.query(Booking).filter(Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    db.delete(b)
    db.commit()
    return {"deleted": booking_id}


# ---------- категории и прайс ----------

@router.get("/categories")
def list_categories(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    if Category is None:
        return []
    counts = {}
    for s in db.query(Service).all():
        counts[s.category_id] = counts.get(s.category_id, 0) + 1
    cats = _sorted(db.query(Category).all(), _order_map(db, "category"))
    return [_cat_out(c, counts) for c in cats]


@router.get("/services")
def list_services(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    cats = {c.id: _cat_out(c) for c in db.query(Category).all()} if Category is not None else {}
    rows = _sorted(db.query(Service).all(), _order_map(db, "service"))
    return [_svc_out(s, cats) for s in rows]


@router.post("/services", status_code=201)
def create_service(payload: ServiceIn, db: Session = Depends(get_db),
                   admin: str = Depends(get_current_admin)):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Название обязательно")
    if Category is not None and not db.query(Category).filter(Category.id == payload.category_id).first():
        raise HTTPException(status_code=404, detail="Категория не найдена")

    s = Service(name=payload.name.strip(), category_id=payload.category_id)
    setattr(s, SVC_PRICE, _price_store(payload.price))
    if SVC_CITIES:
        setattr(s, SVC_CITIES, _cities_store(payload.cities or []))
    if SVC_DESC and payload.description is not None:
        setattr(s, SVC_DESC, payload.description)
    if SVC_ACTIVE:
        setattr(s, SVC_ACTIVE, True if payload.is_active is None else payload.is_active)
    if payload.id is not None:
        s.id = payload.id

    db.add(s)
    db.commit()
    db.refresh(s)
    cats = {c.id: _cat_out(c) for c in db.query(Category).all()} if Category is not None else {}
    return _svc_out(s, cats)


@router.patch("/services/{service_id}")
def patch_service(service_id: int, payload: ServicePatchIn,
                  db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    s = db.query(Service).filter(Service.id == service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    if payload.name is not None:
        if not payload.name.strip():
            raise HTTPException(status_code=400, detail="Название не может быть пустым")
        s.name = payload.name.strip()
    if payload.category_id is not None:
        if Category is not None and not db.query(Category).filter(Category.id == payload.category_id).first():
            raise HTTPException(status_code=404, detail="Категория не найдена")
        s.category_id = payload.category_id
    if payload.price is not None:
        setattr(s, SVC_PRICE, _price_store(payload.price))
    if payload.cities is not None and SVC_CITIES:
        setattr(s, SVC_CITIES, _cities_store(payload.cities))
    if payload.description is not None and SVC_DESC:
        setattr(s, SVC_DESC, payload.description)
    if payload.is_active is not None and SVC_ACTIVE:
        setattr(s, SVC_ACTIVE, payload.is_active)

    db.commit()
    db.refresh(s)
    cats = {c.id: _cat_out(c) for c in db.query(Category).all()} if Category is not None else {}
    return _svc_out(s, cats)


@router.delete("/services/{service_id}")
def remove_service(service_id: int, db: Session = Depends(get_db),
                   admin: str = Depends(get_current_admin)):
    s = db.query(Service).filter(Service.id == service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    db.delete(s)
    row = db.query(AdminOrder).filter(
        AdminOrder.entity == "service", AdminOrder.entity_id == service_id).first()
    if row:
        db.delete(row)
    db.commit()
    return {"deleted": service_id}


@router.post("/services/reorder")
def reorder_services(payload: ReorderIn, db: Session = Depends(get_db),
                     admin: str = Depends(get_current_admin)):
    ids = [int(i) for i in payload.ids]
    existing = {r.entity_id: r for r in
                db.query(AdminOrder).filter(AdminOrder.entity == "service").all()}
    for pos, sid in enumerate(ids):
        if sid in existing:
            existing[sid].position = pos
        else:
            db.add(AdminOrder(entity="service", entity_id=sid, position=pos))
    db.commit()
    return {"ordered": len(ids)}