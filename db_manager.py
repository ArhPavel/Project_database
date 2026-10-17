import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor


class DBManager:
    def __init__(self, db_config):
        self.config = db_config

    def _execute_query(self, query, params=None, fetch_all=True):
        """Вспомогательный метод для безопасного выполнения запросов."""
        conn = psycopg2.connect(**self.config, client_encoding="utf8")
        # Использование DictCursor позволяет обращаться к полям по именам
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            cur.execute(query, params)
            if fetch_all:
                result = [dict(row) for row in cur.fetchall()]
            else:
                res = cur.fetchone()
                result = dict(res) if res else None
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            print(f"Ошибка выполнения запроса: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def get_countries_and_aeroplanes_count(self):
        """Получает список всех стран и количество самолетов."""
        query = """
            SELECT c.name AS country_name, COUNT(a.icao24) AS aeroplanes_count
            FROM countries c
            LEFT JOIN aeroplanes a ON c.id = a.country_id
            GROUP BY c.name
            ORDER BY aeroplanes_count DESC;
        """
        return self._execute_query(query)

    def get_all_aeroplanes(self):
        """Получает список всех воздушных судов."""
        query = """
            SELECT icao24, callsign, origin_country, velocity, latitude, longitude
            FROM aeroplanes;
        """
        return self._execute_query(query)

    def get_avg_speed(self):
        """Получает среднюю скорость по самолетам."""
        query = """
            SELECT AVG(velocity) AS avg_velocity
            FROM aeroplanes
            WHERE velocity IS NOT NULL;
        """
        result = self._execute_query(query, fetch_all=False)
        return float(result["avg_velocity"]) if result and result["avg_velocity"] else 0.0

    def get_aeroplanes_with_higher_speed(self):
        """Получает список всех самолетов, у которых скорость выше средней."""
        query = """
            SELECT icao24, callsign, velocity
            FROM aeroplanes
            WHERE velocity > (
                SELECT AVG(velocity)
                FROM aeroplanes
                WHERE velocity IS NOT NULL
            )
            ORDER BY velocity DESC;
        """
        return self._execute_query(query)

    def get_aeroplanes_with_keyword(self, keyword):
        """Получает список всех самолетов с символами в позывном."""
        query = """
            SELECT icao24, callsign, origin_country
            FROM aeroplanes
            WHERE callsign ILIKE %s;
        """
        return self._execute_query(query, (f"%{keyword}%",))


# --- Демонстрация работы класса ---
if __name__ == "__main__":
    load_dotenv()

    # Безопасно собираем конфигурацию из .env
    DB_CONFIG = {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
    }

    db = DBManager(DB_CONFIG)

    print("\n1. Количество самолетов по странам:")
    print(db.get_countries_and_aeroplanes_count())

    print(f"\n2. Средняя скорость всех ВС: {db.get_avg_speed():.2f} м/с")

    print("\n3. Топ-3 самолета со скоростью выше средней:")
    print(db.get_aeroplanes_with_higher_speed()[:3])

    print("\n4. Поиск самолетов авиакомпании (по ключевому слову 'A'):")
    print(db.get_aeroplanes_with_keyword("A")[:5])
