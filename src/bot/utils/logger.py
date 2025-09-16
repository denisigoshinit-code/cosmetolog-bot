import logging
from datetime import datetime
from pathlib import Path

def setup_logger():
    """Настройка системы логирования"""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Основной логгер
    logger = logging.getLogger('cosmetolog_bot')
    logger.setLevel(logging.INFO)
    
    # Файловый handler
    log_file = log_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Консольный handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Глобальный логгер
logger = setup_logger()

def log_booking(user_id, service_name, date, time):
    """Логирование записи"""
    logger.info(f"BOOKING - User: {user_id}, Service: {service_name}, Date: {date}, Time: {time}")

def log_coupon_creation(user_id, coupon_id, recipient):
    """Логирование создания купона"""
    logger.info(f"COUPON_CREATED - User: {user_id}, CouponID: {coupon_id}, For: {recipient}")

def log_coupon_used(coupon_id, remaining_sessions):
    """Логирование использования купона"""
    logger.info(f"COUPON_USED - CouponID: {coupon_id}, Remaining: {remaining_sessions}")

def log_error(error_message):
    """Логирование ошибок"""
    logger.error(f"ERROR - {error_message}")