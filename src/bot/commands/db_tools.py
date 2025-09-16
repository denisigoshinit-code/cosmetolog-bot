import asyncpg
from datetime import datetime
from bot.utils.logger import logger
from bot.utils.database import get_db_url  # Используем ту же функцию, что и в database.py

async def get_db_stats():
    """Получить статистику по базе данных"""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Статистика записей
        row = await conn.fetchrow("SELECT COUNT(*) FROM appointments")
        appointments_count = row['count'] if row else 0

        # Статистика купонов
        row = await conn.fetchrow("SELECT COUNT(*) FROM coupons")
        coupons_count = row['count'] if row else 0

        # Статистика пользователей
        row = await conn.fetchrow("SELECT COUNT(*) FROM users")
        users_count = row['count'] if row else 0

        # Последние записи
        rows = await conn.fetch("""
            SELECT a.date, a.time, s.name, u.first_name 
            FROM appointments a 
            JOIN services s ON a.service_id = s.id 
            JOIN users u ON a.user_id = u.id 
            ORDER BY a.id DESC LIMIT 5
        """)

        # Преобразуем date объекты в строки для удобства
        recent_appointments = []
        for row in rows:
            recent_appointments.append({
                'date': row['date'],  
                'time': row['time'],
                'service': row['name'],
                'user_name': row['first_name']
            })

        return {
            'appointments': appointments_count,
            'coupons': coupons_count,
            'users': users_count,
            'recent_appointments': recent_appointments
        }
    except Exception as e:
        logger.error(f"Error getting DB stats: {e}")
        return None
    finally:
        await conn.close()

async def export_appointments_to_csv():
    """Экспорт записей в CSV"""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Получаем все записи
        rows = await conn.fetch("""
            SELECT a.date, a.time, s.name, s.price, u.first_name, u.username
            FROM appointments a 
            JOIN services s ON a.service_id = s.id 
            JOIN users u ON a.user_id = u.id 
            ORDER BY a.date, a.time
        """)
        
        # Создаем CSV
        csv_content = "Дата;Время;Услуга;Цена;Имя;Username\n"
        for row in rows:
            # Форматируем строку, экранируя возможные точки с запятой в данных
            date_str = row['date']  # Уже строка
            time = row['time'] or ""
            service = (row['name'] or "").replace(";", ",")
            price = row['price'] or 0
            first_name = (row['first_name'] or "").replace(";", ",")
            username = (row['username'] or "").replace(";", ",")
            
            csv_content += f"{date_str};{time};{service};{price};{first_name};{username}\n"
        
        return csv_content
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return None
    finally:
        await conn.close()

async def get_schedule_for_period(start_date: str, end_date: str):
    """Получить график на период"""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Преобразуем строки в date объекты
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        rows = await conn.fetch("""
            SELECT date, available, time_range, shift_type 
            FROM schedule 
            WHERE date BETWEEN $1 AND $2 
            ORDER BY date
        """, start_dt, end_dt)
        
        # Преобразуем date объекты обратно в строки
        result = []
        for row in rows:
            result.append({
                'date': row['date'].strftime("%Y-%m-%d"),
                'available': row['available'],
                'time_range': row['time_range'],
                'shift_type': row['shift_type']
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        return None
    finally:
        await conn.close()