import os

import psycopg2
import requests
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Теперь конфигурация безопасна и берется из окружения
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")

# Заранее определенные точные координаты (Bounding Boxes) стран
COUNTRY_BOUNDS = {
    "Germany": [47.2701, 55.0991, 5.8663, 15.0418],
    "France": [42.3321, 51.1242, -5.1406, 8.2306],
    "Italy": [35.4897, 47.0920, 6.6267, 18.5203],
    "Spain": [35.1705, 43.7914, -9.3015, 3.3223],
}


def get_opensky_token():
    """Получает Bearer токен для авторизации в OpenSky API согласно OAuth2."""
    url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    data = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}

    # ИСПРАВЛЕНО: Добавлены заголовки, чтобы сервер авторизации не выдавал ошибку 403
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        print(f"Ошибка получения токена OpenSky (проверьте ID и Secret): {e}")
        # Выведем ответ сервера для детальной диагностики, если ошибка повторится
        if "response" in locals() and response.text:
            print(f"Ответ сервера: {response.text[:200]}")
        return None


def fetch_aircraft_in_bbox(bbox, token):
    """Получает самолеты в рамках указанных координат с авторизацией."""
    url = "https://opensky-network.org/api/states/all"

    params = {"lamin": bbox[0], "lamax": bbox[1], "lomin": bbox[2], "lomax": bbox[3]}

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("states", []) or []
        elif response.status_code == 401:
            print("Ошибка: Токен авторизации недействителен.")
            return []
        elif response.status_code == 429:
            print("Превышен лимит запросов (классовые лимиты). Подождите.")
            return []
        else:
            print(f"Ошибка OpenSky API: {response.status_code}")
            return []
    except Exception as e:
        print(f"Не удалось прочитать данные OpenSky API: {e}")
        return []


def init_db_and_load_data():
    """Создает структуру и наполняет базу актуальными данными."""
    token = get_opensky_token()
    if not token:
        print("Загрузка прервана: невозможно авторизоваться в OpenSky.")
        return

    conn = psycopg2.connect(**DB_CONFIG, client_encoding="utf8")
    cur = conn.cursor()

    # Очищаем данные
    cur.execute("TRUNCATE aeroplanes, countries RESTART IDENTITY CASCADE;")

    for country, bbox in COUNTRY_BOUNDS.items():
        print(f"Обработка страны: {country}...")

        cur.execute(
            """
            INSERT INTO countries (name, lat_min, lat_max, lon_min, lon_max)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
            """,
            (country, bbox[0], bbox[1], bbox[2], bbox[3]),
        )
        country_id = cur.fetchone()[0]

        planes = fetch_aircraft_in_bbox(bbox, token)
        print(f"Найдено самолетов в воздухе: {len(planes)}")

        for p in planes:
            # ИСПРАВЛЕНО: Распаковка полей списка p по правильным индексам OpenSky API
            icao24 = p[0]
            callsign = p[1].strip() if p[1] else None
            origin_country = p[2]
            lon = p[5]
            lat = p[6]
            velocity = p[9]

            cur.execute(
                """
                INSERT INTO aeroplanes (icao24, callsign, origin_country, longitude, latitude, velocity, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (icao24) DO NOTHING;
                """,
                (icao24, callsign, origin_country, lon, lat, velocity, country_id),
            )

    conn.commit()
    cur.close()
    conn.close()
    print("Данные успешно загружены в БД!")


if __name__ == "__main__":
    init_db_and_load_data()
