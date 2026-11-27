import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Service, Category

router = APIRouter()


@router.get("/api/services", tags=["services"])
def get_services(city: str | None = Query(None, description="Фильтр по городу (например, korkino)"), db: Session = Depends(get_db)):
    """
    Возвращает список активных услуг.
    Если передан city, фильтрует: оставляет только те, где city есть в списке cities ИЛИ там есть "all".
    """
    # Загружаем услуги вместе с категорией за один запрос
    services = db.query(Service).join(Category).filter(Service.is_active == True).all()
    
    result = []
    for s in services:
        cities_list = json.loads(s.cities)
        
        # Фильтрация по городу
        if city is not None:
            if "all" not in cities_list and city not in cities_list:
                continue
                
        result.append({
            "cat": s.category.slug,
            "catName": s.category.title,
            "name": s.name,
            "price": s.price,
            "unit": s.unit,
            "note": s.note,
            "cities": cities_list
        })
        
    return result