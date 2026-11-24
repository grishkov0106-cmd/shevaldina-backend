# seed.py
# Запускать из корня проекта: python seed.py
# Заливает данные из services.js в базу данных SQLite

import json
from app.database import engine, SessionLocal, Base
from app.models import Category, Service

# Данные, идентичные window.SERVICES и window.CATEGORIES
CATEGORIES_DATA = [
    {"id": "smas", "title": "SMAS-лифтинг", "sort_order": 1},
    {"id": "care", "title": "Уходовые процедуры", "sort_order": 2},
    {"id": "peeling", "title": "Пилинги", "sort_order": 3},
    {"id": "extra", "title": "Дополнительные", "sort_order": 4},
    {"id": "injection", "title": "Инъекционная косметология", "sort_order": 5},
    {"id": "lips", "title": "Аугментация губ", "sort_order": 6},
    {"id": "contour", "title": "Контурная пластика", "sort_order": 7},
    {"id": "botox", "title": "Ботулинотерапия", "sort_order": 8},
    {"id": "face-device", "title": "Аппаратные для лица", "sort_order": 9},
    {"id": "elos", "title": "ЭЛОС-эпиляция", "sort_order": 10},
    {"id": "body-device", "title": "Аппаратные для тела", "sort_order": 11},
    {"id": "hirudo", "title": "Гирудотерапия", "sort_order": 12},
    {"id": "body", "title": "Коррекция тела", "sort_order": 13},
    {"id": "edu", "title": "Обучение", "sort_order": 14},
]

SERVICES_DATA = [
    {"cat": "smas", "name": "Лицо", "price": "20 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Лицо + шея", "price": "25 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Декольте", "price": "10 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Лицо, подбородок, шея, декольте", "price": "30 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Глаза", "price": "10 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Носогубка", "price": "10 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Брыли и подбородок", "price": "14 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Живот", "price": "23 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Живот + бока", "price": "26 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Валики над коленями", "price": "8 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Внутренняя часть бедра", "price": "10 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "От ягодицы до подколенной чашечки", "price": "15 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Ягодицы", "price": "10 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Руки", "price": "12 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "smas", "name": "Кисти рук", "price": "9 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "care", "name": "Уходовая программа", "price": "2 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "care", "name": "Чистка лица ультразвуковая", "price": "1 500", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "care", "name": "Чистка комбинированная", "price": "2 500", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "peeling", "name": "Миндальный (осветляющий / омолаживающий / анти-акне)", "price": "2 500 – 3 500", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "peeling", "name": "Жёлтый пилинг", "price": "3 500", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "peeling", "name": "Curenex Snow Peel (снежный пилинг)", "price": "3 500", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "extra", "name": "Удаление папиллом", "price": "800", "unit": "за шт", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "extra", "name": "Мезонити", "price": "600", "unit": "за шт", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "injection", "name": "Биоревитализация — Хуарон", "price": "3 000", "cities": ["all"]},
    {"cat": "injection", "name": "Реві Стронг", "price": "13 000", "cities": ["all"]},
    {"cat": "injection", "name": "Реві (глаза)", "price": "9 500", "cities": ["all"]},
    {"cat": "injection", "name": "Коктейль Монако", "price": "10 000", "cities": ["all"]},
    {"cat": "injection", "name": "PROFILO", "price": "25 000", "cities": ["all"]},
    {"cat": "injection", "name": "Атлантис (Россия)", "price": "13 000", "cities": ["all"]},
    {"cat": "injection", "name": "Атлантис (глаза)", "price": "12 000", "cities": ["all"]},
    {"cat": "injection", "name": "Антипигментация / плазмолифтинг / биогель (белый)", "price": "5 000", "cities": ["all"]},
    {"cat": "injection", "name": "The star (по точкам)", "price": "8 000", "cities": ["all"]},
    {"cat": "injection", "name": "Biogel cold, white, green", "price": "5 000", "cities": ["all"]},
    {"cat": "injection", "name": "Белотеро Ревайн", "price": "14 000", "cities": ["all"]},
    {"cat": "injection", "name": "Люси ПДРН", "price": "7 500", "cities": ["all"]},
    {"cat": "injection", "name": "Реджува ПДРН", "price": "7 500", "cities": ["all"]},
    {"cat": "injection", "name": "Киаара", "price": "5 000", "cities": ["all"]},
    {"cat": "injection", "name": "Spider Aqua Eye Booster", "price": "6 000", "cities": ["all"]},
    {"cat": "injection", "name": "BioGel White (область глаз)", "price": "2 500", "cities": ["all"]},
    {"cat": "injection", "name": "Липолитик (флакон)", "price": "12 000", "cities": ["all"]},
    {"cat": "injection", "name": "Сужение носа", "price": "3 000", "cities": ["all"]},
    {"cat": "injection", "name": "Анти-алопеция", "price": "13 000", "cities": ["all"]},
    {"cat": "injection", "name": "Барби токс", "price": "8 500", "cities": ["all"]},
    {"cat": "injection", "name": "Приподнятие бровей", "price": "3 000", "cities": ["all"]},
    {"cat": "injection", "name": "Проработка платизмы", "price": "7 000", "cities": ["all"]},
    {"cat": "injection", "name": "Морщины над губой", "price": "2 000", "cities": ["all"]},
    {"cat": "injection", "name": "Гипергидроз подмышек", "price": "13 000", "cities": ["all"]},
    {"cat": "injection", "name": "Плазмолифтинг (сеанс)", "price": "4 500 – 7 000", "cities": ["all"]},
    {"cat": "lips", "name": "Аугментация губ (диапазон)", "price": "10 000 – 19 000", "note": "зависит от препарата", "cities": ["all"]},
    {"cat": "lips", "name": "Корея (Elasty)", "price": "10 000", "cities": ["all"]},
    {"cat": "lips", "name": "Стелаж М", "price": "19 000", "cities": ["all"]},
    {"cat": "lips", "name": "Белотеро", "price": "19 000", "cities": ["all"]},
    {"cat": "lips", "name": "Висколайн (Россия)", "price": "15 000", "cities": ["all"]},
    {"cat": "contour", "name": "Коррекция подбородка филлером", "price": "9 000", "cities": ["all"]},
    {"cat": "contour", "name": "Углы Джоли", "price": "20 000", "cities": ["all"]},
    {"cat": "contour", "name": "Скулы", "price": "20 000", "cities": ["all"]},
    {"cat": "contour", "name": "Фул фейс комплекс", "price": "39 000", "cities": ["all"]},
    {"cat": "contour", "name": "Попа как у Ким", "price": "15 000", "cities": ["all"]},
    {"cat": "contour", "name": "Коллагенотерапия", "price": "14 000 – 20 000", "cities": ["all"]},
    {"cat": "contour", "name": "Детокс точка", "price": "4 000", "cities": ["all"]},
    {"cat": "contour", "name": "Точка стройности", "price": "5 000", "cities": ["all"]},
    {"cat": "botox", "name": "Ботулинотерапия (за единицу)", "price": "от 250 / ед.", "note": "REN tox 250 ед. · Релатокс 350 · Лантокс 300 ед.", "cities": ["all"]},
    {"cat": "face-device", "name": "Фотоомоложение лица", "price": "3 000", "unit": "лицо", "cities": ["korkino"]},
    {"cat": "face-device", "name": "Антикупероз", "price": "600", "unit": "вспышка", "cities": ["korkino"]},
    {"cat": "face-device", "name": "Антиакне", "price": "3 000", "unit": "лицо", "cities": ["korkino"]},
    {"cat": "face-device", "name": "Карбоновый пилинг", "price": "1 500", "unit": "сеанс", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "face-device", "name": "Карбоновый пилинг (курс)", "price": "5 000", "unit": "5 сеансов", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "face-device", "name": "RF-лифтинг", "price": "1 000", "unit": "лицо", "cities": ["korkino"]},
    {"cat": "face-device", "name": "RF-лифтинг", "price": "1 500", "unit": "лицо + шея", "cities": ["korkino"]},
    {"cat": "face-device", "name": "Indiba", "price": "1 000", "unit": "лицо", "cities": ["korkino"]},
    {"cat": "face-device", "name": "Indiba", "price": "1 500", "unit": "лицо и шея", "cities": ["korkino"]},
    {"cat": "face-device", "name": "Игольчатый RF-лифтинг", "price": "10 000", "unit": "лицо", "cities": ["korkino"]},
    {"cat": "face-device", "name": "Игольчатый RF-лифтинг", "price": "13 000", "unit": "лицо, шея, декольте", "cities": ["korkino"]},
    {"cat": "elos", "name": "Подмышки", "price": "700", "cities": ["korkino"]},
    {"cat": "elos", "name": "Голени — бёдра", "price": "1 500", "cities": ["korkino"]},
    {"cat": "elos", "name": "Бикини", "price": "1 200", "cities": ["korkino"]},
    {"cat": "elos", "name": "Глубокое бикини", "price": "1 600", "cities": ["korkino"]},
    {"cat": "elos", "name": "Руки до локтя", "price": "1 000", "cities": ["korkino"]},
    {"cat": "elos", "name": "Руки полностью", "price": "1 400", "cities": ["korkino"]},
    {"cat": "elos", "name": "Спина", "price": "1 500", "cities": ["korkino"]},
    {"cat": "elos", "name": "Живот", "price": "1 000", "cities": ["korkino"]},
    {"cat": "elos", "name": "Ноги до колена", "price": "1 200", "cities": ["korkino"]},
    {"cat": "elos", "name": "Ноги полностью", "price": "1 500", "cities": ["korkino"]},
    {"cat": "elos", "name": "Лицо", "price": "1 500", "cities": ["korkino"]},
    {"cat": "elos", "name": "Над губой", "price": "300", "cities": ["korkino"]},
    {"cat": "elos", "name": "Подбородок", "price": "500", "cities": ["korkino"]},
    {"cat": "elos", "name": "Комплекс: глубокое бикини + подмышки", "price": "2 000", "note": "комплекс", "cities": ["korkino"]},
    {"cat": "elos", "name": "Комплекс: подмышки + бикини + голени", "price": "2 700", "note": "комплекс", "cities": ["korkino"]},
    {"cat": "elos", "name": "Комплекс: подмышки + бикини + ноги полностью", "price": "3 600", "note": "комплекс", "cities": ["korkino"]},
    {"cat": "elos", "name": "Комплекс: подмышки + бикини + руки + ноги полностью", "price": "4 100", "note": "комплекс", "cities": ["korkino"]},
    {"cat": "body-device", "name": "LPG-массаж", "price": "1 000", "unit": "1 сеанс", "cities": ["korkino"]},
    {"cat": "body-device", "name": "LPG-массаж (курс)", "price": "8 500", "unit": "10 сеансов", "cities": ["korkino"]},
    {"cat": "body-device", "name": "Костюм для LPG", "price": "500", "unit": "аренда", "cities": ["korkino"]},
    {"cat": "body-device", "name": "Indiba (жиротоп 2/1)", "price": "2 000", "unit": "1 сеанс", "cities": ["korkino"]},
    {"cat": "body-device", "name": "Indiba (жиротоп 2/1, курс)", "price": "7 500", "unit": "5 сеансов", "cities": ["korkino"]},
    {"cat": "body-device", "name": "Вибрационный массаж тела", "price": "1 000", "unit": "1 сеанс", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Вибрационный массаж (зона)", "price": "600", "unit": "зона", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Вибрационный массаж (курс)", "price": "4 000", "unit": "5 сеансов", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Липосоникс", "price": "6 000", "unit": "раз в месяц", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Липосоникс — живот и бока", "price": "10 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Липосоникс — руки", "price": "5 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Липосоникс — валики над коленями", "price": "3 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Липосоникс — подбородок", "price": "2 500", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Игольчатый RF-лифтинг (тело)", "price": "10 000", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "RF-лифтинг (зона)", "price": "1 500", "unit": "1 сеанс", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "RF-лифтинг (зона, курс)", "price": "5 000", "unit": "5 сеансов", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "EMS-тренировка", "price": "1 500", "unit": "1 зона", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Абонемент: 5 EMS", "price": "7 500", "note": "абонемент", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Комплекс: 10 LPG + 10 EMS", "price": "17 000", "note": "абонемент", "cities": ["korkino"]},
    {"cat": "body-device", "name": "Комплекс: 10 LPG + 5 Indiba 2/1", "price": "16 000", "note": "абонемент", "cities": ["korkino"]},
    {"cat": "body-device", "name": "Комплекс: 10 LPG + 5 EMS", "price": "13 500", "note": "абонемент", "cities": ["korkino"]},
    {"cat": "body-device", "name": "Комплекс: 10 вибрационный + 10 Indiba 2/1", "price": "23 000", "note": "абонемент", "cities": ["korkino"]},
    {"cat": "body-device", "name": "Абонемент только EMS — 10 сессий", "price": "9 000", "note": "абонемент", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body-device", "name": "Абонемент только EMS — 20 сессий", "price": "17 000", "note": "абонемент", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "hirudo", "name": "Оздоровление медицинскими пиявками", "price": "2 000", "unit": "сеанс", "cities": ["korkino", "chelyabinsk"]},
    {"cat": "body", "name": "Липоредукция подбородка", "price": "30 000", "cities": ["all"]},
    {"cat": "body", "name": "Моделирование тела", "price": "Индивидуально", "note": "Подбирается персонально под ваши цели", "cities": ["all"]},
    {"cat": "edu", "name": "Курс «Гирудотерапия»", "price": "15 000", "note": "Сертификат. Очно (К/Ч) или Онлайн.", "cities": ["all"]},
    {"cat": "edu", "name": "Мастер аппаратной коррекции тела", "price": "Индивидуально", "note": "Свидетельство гос. образца и сертификат. Возможно очно (К/Ч) или Онлайн.", "cities": ["all"]},
    {"cat": "edu", "name": "Косметик-эстетист (лицо / тело)", "price": "Индивидуально", "note": "Свидетельство гос. образца и сертификат. Возможно очно (К/Ч) или Онлайн.", "cities": ["all"]},
    {"cat": "edu", "name": "Повышение квалификации", "price": "Индивидуально", "note": "Выдача документов без обучения (аттестация). Возможно Онлайн.", "cities": ["all"]},
]


def seed_db():
    print("🌱 Начинаем наполнение базы данных...")
    
    # Пересоздаём таблицы (очищаем старые данные для чистоты)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Создаём категории
        print("  -> Создаём категории...")
        for cat_data in CATEGORIES_DATA:
            cat = Category(
                slug=cat_data["id"],
                title=cat_data["title"],
                sort_order=cat_data["sort_order"]
            )
            db.add(cat)
        db.commit()
        
        # 2. Создаём услуги
        print("  -> Создаём услуги...")
        for svc_data in SERVICES_DATA:
            # Находим категорию по slug
            category = db.query(Category).filter(Category.slug == svc_data["cat"]).first()
            if not category:
                print(f"  ⚠️ Категория '{svc_data['cat']}' не найдена, пропускаем услугу '{svc_data['name']}'")
                continue
                
            service = Service(
                category_id=category.id,
                name=svc_data["name"],
                price=svc_data["price"],
                unit=svc_data.get("unit"),
                note=svc_data.get("note"),
                cities=json.dumps(svc_data["cities"]),
                is_active=True
            )
            db.add(service)
            
        db.commit()
        print("✅ База данных успешно наполнена!")
        print(f"   Создано категорий: {len(CATEGORIES_DATA)}")
        print(f"   Создано услуг: {len(SERVICES_DATA)}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при наполнении базы: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()