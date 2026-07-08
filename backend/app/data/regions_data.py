"""Геоданные регионов Республики Казахстан для региональной аналитики и карты.

Координаты — административных центров (приближённо), для тепловой карты
дашбордов. Используется enterprise_seed для наполнения таблицы regions.
"""

# name, code, center, lat, lng, population (тыс. чел., приближённо)
KZ_REGIONS_GEO = [
    {"name": "Астана", "code": "AST", "center": "Астана", "lat": 51.1605, "lng": 71.4704, "population": 1350},
    {"name": "Алматы", "code": "ALA", "center": "Алматы", "lat": 43.2220, "lng": 76.8512, "population": 2100},
    {"name": "Шымкент", "code": "SHY", "center": "Шымкент", "lat": 42.3417, "lng": 69.5901, "population": 1200},
    {"name": "Абайская область", "code": "ABA", "center": "Семей", "lat": 50.4111, "lng": 80.2275, "population": 610},
    {"name": "Акмолинская область", "code": "AKM", "center": "Кокшетау", "lat": 53.2872, "lng": 69.3900, "population": 780},
    {"name": "Актюбинская область", "code": "AKT", "center": "Актобе", "lat": 50.2839, "lng": 57.1670, "population": 920},
    {"name": "Алматинская область", "code": "ALM", "center": "Конаев", "lat": 43.8600, "lng": 77.0700, "population": 1450},
    {"name": "Атырауская область", "code": "ATY", "center": "Атырау", "lat": 47.0945, "lng": 51.9238, "population": 690},
    {"name": "Восточно-Казахстанская область", "code": "VKO", "center": "Усть-Каменогорск", "lat": 49.9481, "lng": 82.6279, "population": 740},
    {"name": "Жамбылская область", "code": "ZHA", "center": "Тараз", "lat": 42.9000, "lng": 71.3667, "population": 1180},
    {"name": "Жетысуская область", "code": "ZHE", "center": "Талдыкорган", "lat": 45.0156, "lng": 78.3739, "population": 700},
    {"name": "Западно-Казахстанская область", "code": "ZKO", "center": "Уральск", "lat": 51.2270, "lng": 51.3865, "population": 680},
    {"name": "Карагандинская область", "code": "KAR", "center": "Караганда", "lat": 49.8047, "lng": 73.1094, "population": 1130},
    {"name": "Костанайская область", "code": "KOS", "center": "Костанай", "lat": 53.2144, "lng": 63.6246, "population": 830},
    {"name": "Кызылординская область", "code": "KYZ", "center": "Кызылорда", "lat": 44.8488, "lng": 65.4823, "population": 820},
    {"name": "Мангистауская область", "code": "MAN", "center": "Актау", "lat": 43.6410, "lng": 51.1980, "population": 750},
    {"name": "Павлодарская область", "code": "PAV", "center": "Павлодар", "lat": 52.2870, "lng": 76.9674, "population": 760},
    {"name": "Северо-Казахстанская область", "code": "SKO", "center": "Петропавловск", "lat": 54.8666, "lng": 69.1500, "population": 530},
    {"name": "Туркестанская область", "code": "TUR", "center": "Туркестан", "lat": 43.3017, "lng": 68.2517, "population": 2050},
    {"name": "Улытауская область", "code": "ULY", "center": "Жезказган", "lat": 47.7833, "lng": 67.7000, "population": 220},
]

REGION_NAMES = [r["name"] for r in KZ_REGIONS_GEO]

# Быстрый доступ: имя региона -> (широта, долгота) административного центра.
REGION_COORDS: dict[str, tuple[float, float]] = {
    r["name"]: (r["lat"], r["lng"]) for r in KZ_REGIONS_GEO
}

# Географический центр Казахстана — запасные координаты.
KZ_CENTER: tuple[float, float] = (48.0196, 66.9237)


def coords_for_region(name: str | None, *, jitter: float = 0.0, rng=None) -> tuple[float, float]:
    """Координаты для региона по имени; при jitter>0 добавляет детерминированный разброс.

    Используется для наполнения карты обращений синтетическими данными: каждое
    обращение получает точку рядом с административным центром своего региона.
    """
    base = REGION_COORDS.get(name or "")
    if base is None and name:
        for region_name, coords in REGION_COORDS.items():
            if name in region_name or region_name in name:
                base = coords
                break
    if base is None:
        base = KZ_CENTER
    lat, lng = base
    if jitter and rng is not None:
        lat += rng.uniform(-jitter, jitter)
        lng += rng.uniform(-jitter, jitter)
    return round(lat, 6), round(lng, 6)
