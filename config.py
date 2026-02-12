import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем .env файл
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Конфигурация бота"""
    
    # Получаем токен из .env
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    
    # Получаем ID админа из .env
    try:
        ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
    except (ValueError, TypeError):
        ADMIN_ID = 0

config = Config()

# Проверка конфигурации
if not config.BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в .env файле!")
    print("📁 Создайте файл .env и добавьте строку: BOT_TOKEN=ваш_токен_здесь")
    exit(1)

if not config.ADMIN_ID:
    print("❌ ОШИБКА: ADMIN_ID не найден в .env файле!")
    print("📁 Создайте файл .env и добавьте строку: ADMIN_ID=ваш_id_здесь")
    exit(1)

print(f"✅ Конфигурация загружена:")
print(f"   BOT_TOKEN: {config.BOT_TOKEN[:10]}...")
print(f"   ADMIN_ID: {config.ADMIN_ID}")