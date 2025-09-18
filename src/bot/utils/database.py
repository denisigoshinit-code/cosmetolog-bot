import asyncpg
import os
from pathlib import Path
from datetime import datetime, timedelta, date  
import random
import string
import logging

logger = logging.getLogger(__name__)

def get_db_url():
    """Возвращает строку подключения к PostgreSQL из переменной окружения."""
    return os.getenv("DATABASE_URL", "postgresql://bot_user:password@localhost:5432/cosmetolog_prod")

# Константы для типов купонов
COUPON_TYPES = {
    "1": {"name": "💎 Глубокое очищение", "price": 3500, "base_price": 3500},
    "2": {"name": "🔁 Перезагрузка кожи", "price": 6000, "base_price": 6000},
    "3": {"name": "✨ Жена миллионера", "price": 5000, "base_price": 5000}
}

CONTACT_METHODS = {
    "1": "Telegram",
    "2": "Телефон",
    "3": "Личная передача"
}

async def init_db():
    """Инициализирует базу данных: создаёт таблицы и заполняет начальными данными."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Создаём таблицы
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                first_name TEXT,
                username TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                service_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                UNIQUE(date, time)
            )
        """)
        # 🚀 ПОЛНОСТЬЮ ОБНОВЛЁННАЯ ТАБЛИЦА КУПОНОВ СО ВСЕМИ НЕОБХОДИМЫМИ ПОЛЯМИ
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id TEXT PRIMARY KEY,
                user_id BIGINT, -- ID пользователя, который создал купон
                sender TEXT NOT NULL, -- Кто дарит
                recipient TEXT NOT NULL, -- Кому дарят
                contact_method TEXT, -- Способ связи (Telegram, Телефон и т.д.)
                contact_info TEXT, -- Контактная информация
                service TEXT NOT NULL, -- Название услуги
                price INTEGER NOT NULL, -- Общая цена
                sessions INTEGER NOT NULL DEFAULT 1, -- Количество сеансов
                used INTEGER NOT NULL DEFAULT 0, -- Сколько сеансов уже использовано
                status TEXT NOT NULL DEFAULT 'Ожидает подтверждения', -- Статус купона
                paid TEXT NOT NULL DEFAULT 'Нет', -- Оплачен ли купон
                created_at TIMESTAMP DEFAULT NOW() -- Дата создания
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                date DATE PRIMARY KEY,
                available TEXT NOT NULL,
                time_range TEXT NOT NULL,
                shift_type TEXT NOT NULL,
                available_times TEXT NOT NULL
            )
        """)

        # Заполняем услуги
        services = [
            (1, "💧 Рост волос под плазмой", 3500, "Стимулируем рост волос с помощью холодной плазмы. Без боли, без реабилитации. Уже после 3 сеансов — меньше выпадения и больше густоты."),
            (2, "🔁 Перезагрузка кожи", 2000, "Глубокий пилинг, подобранный под ваш тип кожи. Снимаем усталость, тусклость и неровный тон. Кожа сияет уже после первого сеанса."),
            (3, "✨ Пилинг с ретинолом", 3000, "Антивозрастной пилинг, который разглаживает мелкие морщинки, улучшает текстуру и делает кожу упругой. Для тех, кто хочет выглядеть на 5 лет моложе."),
            (4, "💎 Глубокое очищение", 3500, "Комбинированная чистка на профессиональной косметике Christina (Израиль). Избавляем от чёрных точек, акне и расширенных пор. Кожа дышит и сияет."),
            (5, "⚡ Кислородный всплеск", 2500, "Карбокситерапия — мощный заряд CO₂ для кожи. Уходит тусклость, появляется сияние и здоровый цвет лица. Как после отпуска!"),
            (6, "🌙 Молодая кожа без игл", 3500, "Холодная плазма для лица и шеи. Безинъекционное омоложение: подтягиваем овал, улучшаем упругость, уменьшаем морщины."),
            (7, "🤍 Декольте", 1500, "Уход за зоной декольте — часто забываемой, но очень заметной. Увлажняем, выравниваем тон, убираем пигментацию."),
            (8, "🤲 Руки красоты", 2500, "Ваши руки расскажут о вас больше, чем вы думаете. Восстановим упругость, уберём пигментацию и сухость."),
            (9, "🌞 Плоский живот", 2500, "Процедура для упругости и тонуса кожи живота. Подходит после родов или снижения веса. Цена от 2500 ₽ за сеанс."),
            (10, "✅ Чистая кожа", 300, "Аккуратное удаление папилом. Без шрамов, безопасно, быстро. От 10 шт. — по 150 ₽"),
            (11, "🩹 Удаление шипиц", 350, "Эффективное и щадящее удаление шипиц. Не оставляет следов, заживление за 3–5 дней."),
            (12, "✨ Жена миллионера", 5000, "Биоревитализация — инъекции гиалуроновой кислоты для глубокого увлажнения и сияния кожи. Как после СПА на 2 недели вперед. Препарат подбирается индивидуально."),
            (13, "💬 Консультация по омоложению", 0, "Запишитесь на бесплатную консультацию — обсудим, какие процедуры подойдут именно вам. Без навязывания."),
            (14, "💋 Коррекция губ", 0, "Подберём идеальный объём и форму. Натурально, красиво, без перебора."),
            (15, "🔄 Филлеры", 0, "Индивидуальный подход. Только то, что нужно — без лишнего.")
        ]

        await conn.executemany("""
            INSERT INTO services (id, name, price, description) 
            VALUES ($1, $2, $3, $4) 
            ON CONFLICT (id) DO UPDATE SET 
                name = EXCLUDED.name, 
                price = EXCLUDED.price, 
                description = EXCLUDED.description
        """, services)
    finally:
        await conn.close()

    # Генерируем график на 90 дней вперед
    await generate_schedule()

def generate_coupon_id():
    """Генерирует уникальный ID для купона."""
    return f"GC-{''.join(random.choices(string.digits, k=5))}"

async def generate_schedule():
    """Генерирует график работы на 90 дней вперёд и сохраняет в БД."""
    from .schedule_generator import generate_schedule_data

    conn = await asyncpg.connect(get_db_url())
    try:
        schedule_data = generate_schedule_data()
        for date_str, schedule_info in schedule_data.items():
            # Преобразуем строку даты в объект date
            schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            available_times = ",".join(schedule_info["times"])
            
            await conn.execute("""
                INSERT INTO schedule (date, available, time_range, shift_type, available_times) 
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (date) DO UPDATE SET
                    available = EXCLUDED.available,
                    time_range = EXCLUDED.time_range,
                    shift_type = EXCLUDED.shift_type,
                    available_times = EXCLUDED.available_times
            """, schedule_date, schedule_info["available"], schedule_info["time_range"], schedule_info["type"], available_times)
    finally:
        await conn.close()

# --- Основные функции для работы с БД ---

async def get_services():
    """Возвращает список всех услуг."""
    conn = await asyncpg.connect(get_db_url())
    try:
        rows = await conn.fetch("SELECT id, name, price, description FROM services ORDER BY id")
        return rows
    finally:
        await conn.close()

async def get_service_name(service_id: int) -> str:
    """Возвращает название услуги по её ID."""
    conn = await asyncpg.connect(get_db_url())
    try:
        row = await conn.fetchrow("SELECT name FROM services WHERE id = $1", service_id)
        return row['name'] if row else "Неизвестная услуга"
    finally:
        await conn.close()

async def get_service_price(service_id: int) -> float:
    """Возвращает цену услуги по её ID."""
    conn = await asyncpg.connect(get_db_url())
    try:
        row = await conn.fetchrow("SELECT price FROM services WHERE id = $1", service_id)
        return row['price'] if row else 0.0
    finally:
        await conn.close()

async def add_user(user_id: int, first_name: str, username: str):
    """Добавляет или обновляет информацию о пользователе."""
    conn = await asyncpg.connect(get_db_url())
    try:
        await conn.execute("""
            INSERT INTO users (id, first_name, username) 
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET 
                first_name = EXCLUDED.first_name,
                username = EXCLUDED.username
        """, user_id, first_name, username)
    finally:
        await conn.close()

async def is_time_available(date_input, time: str) -> bool:
    """Проверяет, свободно ли указанное время для записи."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Всегда преобразуем в строку, так как в таблице appointments поле date - TEXT
        if isinstance(date_input, str):
            date_str = date_input
        else:
            date_str = date_input.strftime("%Y-%m-%d")  # Преобразуем объект date в строку
            
        row = await conn.fetchrow("SELECT 1 FROM appointments WHERE date = $1 AND time = $2", date_str, time)
        return row is None
    except Exception as e:
        logger.error(f"Error checking time availability: {e}")
        return False
    finally:
        await conn.close()

async def is_time_in_schedule(date_str: str, time: str) -> bool:
    """Проверяет, входит ли указанное время в рабочий график дня."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Преобразуем строку в date объект
        schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        row = await conn.fetchrow("SELECT available_times FROM schedule WHERE date = $1", schedule_date)
        if not row:
            return False
        available_times = row['available_times'].split(",")
        return time in available_times
    except Exception as e:
        logger.error(f"Error checking schedule: {e}")
        return False
    finally:
        await conn.close()

async def create_appointment(user_id: int, service_id: int, date_str: str, time: str):
    """Создаёт новую запись на приём."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Просто сохраняем строку, не преобразуем в date
        await conn.execute(
            "INSERT INTO appointments (user_id, service_id, date, time) VALUES ($1, $2, $3, $4)",
            user_id, service_id, date_str, time  # Передаем строку
        )
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise
    finally:
        await conn.close()

async def get_user_appointments(user_id: int):
    """Возвращает список будущих записей пользователя."""
    conn = await asyncpg.connect(get_db_url())
    try:
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        # ВСЁ! ТОЛЬКО ДОБАВИЛ $2 и $3 в WHERE
        rows = await conn.fetch("""
            SELECT a.id, a.date, a.time, s.name
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            WHERE a.user_id = $1
              AND (
                a.date > $2 OR 
                (a.date = $2 AND a.time >= $3)
              )
            ORDER BY a.date, a.time
        """, user_id, today_str, current_time_str)

        return rows  

    except Exception as e:
        logger.error(f"DB_ERROR get_user_appointments: {e}")
        return []
    finally:
        await conn.close()

async def cancel_appointment(appointment_id: int, user_id: int):
    """Отменяет запись пользователя по ID записи."""
    conn = await asyncpg.connect(get_db_url())
    try:
        await conn.execute(
            "DELETE FROM appointments WHERE id = $1 AND user_id = $2",
            appointment_id, user_id
        )
    finally:
        await conn.close()

async def get_available_dates(days_ahead: int = 30):
    """Возвращает список доступных дат для записи на ближайшие N дней."""
    conn = await asyncpg.connect(get_db_url())
    try:
        rows = await conn.fetch("""
            SELECT date, shift_type, available_times 
            FROM schedule 
            WHERE date >= CURRENT_DATE 
            AND available_times != '' 
            ORDER BY date 
            LIMIT $1
        """, days_ahead)
        
        result = []
        for row in rows:
            # date уже объект date, преобразуем в строку
            result.append({
                'date': row['date'].strftime("%Y-%m-%d"),  # Преобразуем в строку
                'shift_type': row['shift_type'],
                'available_times': row['available_times']
            })
        return result
    except Exception as e:
        logger.error(f"Error getting available dates: {e}")
        return []
    finally:
        await conn.close()

async def get_available_times(date_str: str):
    """Возвращает список доступных временных слотов для указанной даты."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Преобразуем строку в date объект
        schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        row = await conn.fetchrow("SELECT available_times FROM schedule WHERE date = $1", schedule_date)
        if not row or not row['available_times']:
            return []
        return row['available_times'].split(",")
    except Exception as e:
        logger.error(f"Error getting available times: {e}")
        return []
    finally:
        await conn.close()

# --- Функции для работы с купонами ---

async def create_coupon(user_id: int, sender: str, recipient: str, contact: str, service_id: int, sessions: int):
    """Создаёт новый подарочный купон."""
    coupon_id = generate_coupon_id()
    base_price = await get_service_price(service_id)
    service_name = await get_service_name(service_id)
    
    # Расчет общей цены
    if sessions == 1:
        total_price = base_price
    elif sessions == 3:
        total_price = int(base_price * 3 * 0.9)  # -10%
    else:  # 5 сеансов
        total_price = int(base_price * 5 * 0.85)  # -15%

    conn = await asyncpg.connect(get_db_url())
    try:
        await conn.execute("""
            INSERT INTO coupons (id, user_id, sender, recipient, contact_info, service, price, sessions, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        """, coupon_id, user_id, sender, recipient, contact, service_name, total_price, sessions)
    finally:
        await conn.close()

    return coupon_id

async def get_user_coupons(user_id: int):
    """Возвращает список купонов, созданных пользователем."""
    conn = await asyncpg.connect(get_db_url())
    try:
        rows = await conn.fetch("""
            SELECT id, service, price, sessions, used, status, paid
            FROM coupons
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, user_id)
        return [dict(row) for row in rows]  # ДОБАВЬ ЭТУ СТРОКУ
    finally:
        await conn.close()

async def use_coupon(coupon_id: str, user_id: int):
    """Использует один сеанс по купону."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Получаем текущее состояние купона
        row = await conn.fetchrow("""
            SELECT used, sessions, status FROM coupons WHERE id = $1
        """, coupon_id)
        
        if not row:
            return None
            
        used, total_sessions, status = row['used'], row['sessions'], row['status']
        
        # Проверяем статус и количество использований
        if status != 'Активен':
            return None
        if used >= total_sessions:
            return None
            
        # Увеличиваем счетчик использований
        new_used = used + 1
        await conn.execute("""
            UPDATE coupons SET used = $1 WHERE id = $2
        """, new_used, coupon_id)
        
        # Если все сеансы использованы, меняем статус
        if new_used >= total_sessions:
            await conn.execute("""
                UPDATE coupons SET status = 'Завершён' WHERE id = $1
            """, coupon_id)
            
        return total_sessions - new_used
    finally:
        await conn.close()

# --- Админские функции  ---

async def get_all_coupons():
    """Возвращает список всех купонов."""
    conn = await asyncpg.connect(get_db_url())
    try:
        rows = await conn.fetch("""
            SELECT id, sender, recipient, contact_info, service, price, status, paid, sessions, used, created_at
            FROM coupons
            ORDER BY created_at DESC
        """)
        return rows
    finally:
        await conn.close()

async def get_today_appointments():
    """Получает записи на сегодня."""
    conn = await asyncpg.connect(get_db_url())
    try:
        today = datetime.now().strftime("%Y-%m-%d")  
        rows = await conn.fetch("""
            SELECT a.date, a.time, s.name, u.first_name, u.username, u.id AS user_id
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN users u ON a.user_id = u.id
            WHERE a.date = $1 
            ORDER BY a.time
        """, today)
        
        result = []
        for row in rows:
            result.append({
                'date': row['date'],  
                'time': row['time'],
                'service': row['name'],
                'user_name': row['first_name'],
                'username': row['username'],
                'user_id': row['user_id']
            })
        return result
    except Exception as e:
        logger.error(f"Error getting today appointments: {e}")
        return []
    finally:
        await conn.close()

async def get_tomorrow_appointments():
    """Получает записи на завтра."""
    conn = await asyncpg.connect(get_db_url())
    try:
        tomorrow = (datetime.now() + timedelta(days=1)).date().strftime("%Y-%m-%d")  # Преобразуем в строку
        rows = await conn.fetch("""
            SELECT a.date, a.time, s.name, u.first_name, u.username, u.id AS user_id
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN users u ON a.user_id = u.id
            WHERE a.date = $1
        """, tomorrow)  # Передаем строку
        
        result = []
        for row in rows:
            result.append({
                'date': row['date'],
                'time': row['time'],
                'service': row['name'],
                'user_name': row['first_name'],
                'username': row['username'],
                'user_id': row['user_id']
            })
        return result
    except Exception as e:
        logger.error(f"Error getting tomorrow appointments: {e}")
        return []
    finally:
        await conn.close()

async def get_week_appointments():
    """Получает записи на ближайшую неделю."""
    conn = await asyncpg.connect(get_db_url())
    try:
        today = datetime.now().date().strftime("%Y-%m-%d")  # Преобразуем в строку
        week_later = (datetime.now() + timedelta(days=7)).date().strftime("%Y-%m-%d")  # Преобразуем в строку
        
        rows = await conn.fetch("""
            SELECT a.date, a.time, s.name, u.first_name, u.username, u.id AS user_id
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN users u ON a.user_id = u.id
            WHERE a.date BETWEEN $1 AND $2
            ORDER BY a.date, a.time
        """, today, week_later)
        
        result = []
        for row in rows:
            result.append({
                'date': row['date'],
                'time': row['time'],
                'service': row['name'],
                'user_name': row['first_name'],
                'username': row['username'],
                'user_id': row['user_id']
            })
        return result
    except Exception as e:
        logger.error(f"Error getting week appointments: {e}")
        return []
    finally:
        await conn.close()

async def mark_coupon_paid(coupon_id: str):
    """Помечает купон как оплаченный."""
    conn = await asyncpg.connect(get_db_url())
    try:
        await conn.execute("""
            UPDATE coupons SET status = 'Активен', paid = 'Да' WHERE id = $1
        """, coupon_id)
    finally:
        await conn.close()

async def reject_coupon(coupon_id: str):
    """Отклоняет купон."""
    conn = await asyncpg.connect(get_db_url())
    try:
        await conn.execute("""
            UPDATE coupons SET status = 'Отклонён' WHERE id = $1
        """, coupon_id)
    finally:
        await conn.close()

async def update_schedule_date(date_str: str, status: str, time_range: str):
    """Обновляет график для конкретной даты."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Преобразуем строку в date объект
        schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Генерируем доступное время в зависимости от статуса
        if status == "Нет":
            times = []
        elif status == "До 18:00":
            times = [f"{h:02d}:00" for h in range(10, 16)]  # 10:00 - 16:00
        else:  # "Да"
            times = [f"{h:02d}:00" for h in range(9, 19)]   # 9:00 - 19:00

        times_str = ",".join(times)

        await conn.execute("""
            INSERT INTO schedule (date, available, time_range, shift_type, available_times) 
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (date) DO UPDATE SET
                available = EXCLUDED.available,
                time_range = EXCLUDED.time_range,
                shift_type = EXCLUDED.shift_type,
                available_times = EXCLUDED.available_times
        """, schedule_date, status, time_range, "Ручное изменение", times_str)
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        raise
    finally:
        await conn.close()

async def create_coupon_with_details(user_id: int, coupon_type: str, sessions: int, 
                                   recipient: str, contact_method: str, contact_info: str, sender: str):
    """Создает купон со всеми деталями (расширенная версия)."""
    coupon_id = generate_coupon_id()
    service_data = COUPON_TYPES[coupon_type]

    # Расчет цены со скидкой
    if sessions == 1:
        price = service_data["base_price"]
    elif sessions == 3:
        price = int(service_data["base_price"] * 3 * 0.9)  # -10%
    else:  # 5 сеансов
        price = int(service_data["base_price"] * 5 * 0.85)  # -15%

    conn = await asyncpg.connect(get_db_url())
    try:
        await conn.execute("""
            INSERT INTO coupons (id, user_id, sender, recipient, contact_method, contact_info, 
                               service, price, sessions, status, paid, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        """, coupon_id, user_id, sender, recipient, contact_method, contact_info,
              service_data["name"], price, sessions, "Ожидает подтверждения", "Нет")
    finally:
        await conn.close()

    return coupon_id, price

async def get_coupon_by_id(coupon_id: str):
    """Получает купон по ID."""
    conn = await asyncpg.connect(get_db_url())
    try:
        row = await conn.fetchrow("SELECT * FROM coupons WHERE id = $1", coupon_id)
        if row:
            # Преобразуем в словарь
            return dict(row)
        return None
    finally:
        await conn.close()

async def update_coupon_status(coupon_id: str, status: str, paid: str = None):
    """Обновляет статус купона."""
    conn = await asyncpg.connect(get_db_url())
    try:
        if paid:
            await conn.execute("""
                UPDATE coupons SET status = $1, paid = $2 WHERE id = $3
            """, status, paid, coupon_id)
        else:
            await conn.execute("""
                UPDATE coupons SET status = $1 WHERE id = $2
            """, status, coupon_id)
    except Exception as e:
        logger.error(f"Error updating coupon status: {e}")
        raise
    finally:
        await conn.close()

async def get_pending_coupons():
    """Получает купоны, ожидающие подтверждения."""
    conn = await asyncpg.connect(get_db_url())
    try:
        rows = await conn.fetch("""
            SELECT * FROM coupons WHERE status = 'Ожидает подтверждения' ORDER BY created_at DESC
        """)
        return [dict(row) for row in rows]  # Преобразуем в словари
    finally:
        await conn.close()

async def get_payment_coupons():
    """Получает купоны, ожидающие оплаты."""
    conn = await asyncpg.connect(get_db_url())
    try:
        rows = await conn.fetch("""
            SELECT * FROM coupons WHERE status = 'Ожидает оплаты' ORDER BY created_at DESC
        """)
        return [dict(row) for row in rows]  # ДОБАВЬ ЭТУ СТРОКУ
    finally:
        await conn.close()

async def get_active_coupons():
    """Получает активные купоны."""
    conn = await asyncpg.connect(get_db_url())
    try:
        rows = await conn.fetch("""
            SELECT * FROM coupons WHERE status = 'Активен' ORDER BY created_at DESC
        """)
        return [dict(row) for row in rows]  # ДОБАВЬ ЭТУ СТРОКУ
    finally:
        await conn.close()

async def use_coupon_session(coupon_id: str):
    """Отмечает использование одного сеанса купона."""
    return await use_coupon(coupon_id, None)  # Используем основную функцию

async def is_date_available(date_str: str) -> bool:
    """Проверяет, доступна ли дата для записи."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Преобразуем строку в date объект
        schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        row = await conn.fetchrow("SELECT available FROM schedule WHERE date = $1", schedule_date)
        if not row:
            return False
        return row['available'] in ["Да", "До 18:00"]
    except Exception as e:
        logger.error(f"Error checking date availability: {e}")
        return False
    finally:
        await conn.close()

async def get_available_time_slots(date_str: str) -> list:
    """Получает доступные временные слоты для даты."""
    conn = await asyncpg.connect(get_db_url())
    try:
        # Преобразуем строку в date объект
        schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        row = await conn.fetchrow("SELECT available_times FROM schedule WHERE date = $1", schedule_date)
        if not row or not row['available_times']:
            return []
        return row['available_times'].split(",")
    except Exception as e:
        logger.error(f"Error getting available times: {e}")
        return []
    finally:
        await conn.close()