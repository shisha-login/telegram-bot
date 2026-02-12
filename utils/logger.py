import logging
import sys
from pathlib import Path

def setup_logger():
    """Настройка логирования для VS Code"""
    
    # Создаем папку для логов если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Вывод в консоль (для VS Code)
            logging.StreamHandler(sys.stdout),
            # Запись в файл
            logging.FileHandler(
                log_dir / 'bot.log',
                encoding='utf-8',
                mode='a'
            )
        ]
    )
    
    # Отключаем лишние логи от библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)