from datetime import datetime, timedelta

def generate_schedule_data():
    """Генерирует график согласно указанной схеме начиная с 12.09"""
    schedule = {}
    
    # Жёстко задаём начальную дату - 12 сентября 2025
    start_date = datetime(2025, 9, 12).date()
    
    # Начинаем с дня 1 цикла (12.09 - Дневная смена)
    cycle_start_index = 0
    
    for i in range(365):  # На 90 дней вперед от 12.09
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Определяем позицию в цикле (8-дневный цикл)
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