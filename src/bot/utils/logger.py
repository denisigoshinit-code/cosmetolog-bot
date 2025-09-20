# src/bot/utils/logger.py
import logging
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / f"bot_{datetime.now().strftime('%Y-%m-%d')}.log"

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d "
    "| USER=%(user_id)s CHAT=%(chat_id)s | %(message)s"
)

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.user_id = getattr(record, 'user_id', 'N/A')
        record.chat_id = getattr(record, 'chat_id', 'N/A')
        return True

# Создаём логгер
def setup_logger():
    logger = logging.getLogger('cosmetolog_bot')
    if logger.handlers:
        return logger  # Избегаем дублирования

    logger.setLevel(logging.INFO)
    logger.addFilter(ContextFilter())

    # Файл-хендлер с ротацией
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)

    # Консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    logger.addHandler(console_handler)

    return logger

# Глобальный логгер
logger = setup_logger()

# Универсальная функция логирования
def log(user_id: int = None, chat_id: int = None, action: str = "", **kwargs):
    """
    Логирует событие с контекстом.
    Пример: log(user_id=message.from_user.id, action="appointment_created", appointment_id=123)
    """
    extra = {"user_id": user_id, "chat_id": chat_id}
    msg = action
    if kwargs:
        details = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        msg += f" | {details}"
    
    logger.info(msg, extra=extra)