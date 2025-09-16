# bot/utils/schedule_manager.py
from datetime import datetime, timedelta
import logging
from .database import get_db_url
from .schedule_generator import generate_schedule_data
import asyncpg

logger = logging.getLogger(__name__)

async def get_last_schedule_date():
    """
    Получает последнюю дату из таблицы schedule.
    Возвращает объект date или None.
    """
    conn = await asyncpg.connect(get_db_url())
    try:
        row = await conn.fetchrow("""
            SELECT MAX(date) FROM schedule
        """)
        if row and row[0]:
            # Преобразуем строку из БД в объект date
            return datetime.strptime(row[0], "%Y-%m-%d").date()
        return None
    except Exception as e:
        logger.error(f"Error getting last schedule date: {e}")
        return None
    finally:
        await conn.close()

def generate_schedule_data_from_date(start_date):
    """
    Генерирует график на 90 дней, начиная с заданной даты.
    Использует ту же логику, что и generate_schedule_data,
    но начинает не с 12.09.2025, а со start_date.
    
    Args:
        start_date (date): Дата, с которой нужно начать генерацию.
        
    Returns:
        dict: Словарь с расписанием.
    """
    schedule = {}
    
    # Определяем позицию в 8-дневном цикле для start_date
    # Это нужно, чтобы продолжить цикл с нужного места
    base_start_date = datetime(2025, 9, 12).date()  # Начало цикла
    days_diff = (start_date - base_start_date).days
    cycle_start_index = days_diff % 8
    
    for i in range(90):  # На 90 дней вперёд
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Определяем позицию в цикле
        cycle_position = (cycle_start_index + i) % 8
        
        if cycle_position in [0, 1]:
            # Дни 1-2: "Нет" (Дневная смена)
            schedule_info = {
                "available": "Нет", 
                "time_range": "—", 
                "type": "Дневная смена", 
                "times": []
            }
        elif cycle_position in [2, 3]:
            # Дни 3-4: "До 18:00" (Ночная смена)
            schedule_info = {
                "available": "До 18:00", 
                "time_range": "10:00 – 16:00", 
                "type": "Ночная смена (начинается в 18:00)", 
                "times": [f"{h:02d}:00" for h in range(10, 16)]
            }
        else:
            # Дни 5-8: "Да" (Выходной → работа)
            schedule_info = {
                "available": "Да", 
                "time_range": "09:00 – 19:00", 
                "type": "Выходной → работа", 
                "times": [f"{h:02d}:00" for h in range(9, 19)]
            }
        
        schedule[date_str] = schedule_info
    
    return schedule

async def auto_extend_schedule():
    """
    Автоматически продлевает график на следующие 90 дней.
    Вызывается из планировщика.
    """
    logger.info("🔄 Начинаю проверку графика...")
    
    try:
        last_date = await get_last_schedule_date()
        if not last_date:
            logger.warning("❌ Не удалось получить последнюю дату графика.")
            return
        
        # Если до конца меньше 7 дней — генерируем новый блок
        days_until_end = (last_date - datetime.now().date()).days
        if days_until_end < 7:
            new_start_date = last_date + timedelta(days=1)
            logger.info(f"📅 До конца графика {days_until_end} дней. Запускаю продление с {new_start_date}...")
            
            new_schedule_data = generate_schedule_data_from_date(new_start_date)
            conn = await asyncpg.connect(get_db_url())
            try:
                for date_str, schedule_info in new_schedule_data.items():
                    available_times = ",".join(schedule_info["times"])
                    
                    await conn.execute("""
                        INSERT INTO schedule (date, available, time_range, shift_type, available_times) 
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (date) DO UPDATE SET
                            available = EXCLUDED.available,
                            time_range = EXCLUDED.time_range,
                            shift_type = EXCLUDED.shift_type,
                            available_times = EXCLUDED.available_times
                    """, date_str, schedule_info["available"], schedule_info["time_range"], schedule_info["type"], available_times)
                
                logger.info(f"✅ График успешно продлён с {new_start_date.strftime('%Y-%m-%d')}")
            except Exception as e:
                logger.error(f"❌ Ошибка при сохранении нового графика: {e}")
            finally:
                await conn.close()
        else:
            logger.info(f"📅 График в порядке. До конца: {days_until_end} дней.")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при продлении графика: {e}")