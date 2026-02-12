#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Добавляем корневую папку в путь
sys.path.append(str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.enums import ParseMode

# Импортируем конфигурацию
from config import config
from utils.logger import setup_logger
from handlers import user, admin

# Настраиваем логирование
logger = setup_logger()

async def set_bot_commands(bot: Bot):
    """Установка команд бота"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="📋 Помощь"),
    ]
    await bot.set_my_commands(commands)

async def main():
    """Главная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("🚀 Запуск Telegram бота...")
    logger.info("=" * 50)
    
    try:
        # Создаем экземпляры бота и диспетчера
        bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
        dp = Dispatcher()
        
        # Регистрируем роутеры
        dp.include_router(user.router)
        dp.include_router(admin.router)
        
        # Устанавливаем команды
        await set_bot_commands(bot)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот @{bot_info.username} запущен!")
        logger.info(f"🆔 ID бота: {bot_info.id}")
        logger.info(f"👤 Админ: {config.ADMIN_ID}")
        logger.info("📡 Polling...")
        logger.info("=" * 50)
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("⏹ Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        if 'bot' in locals():
            await bot.session.close()
            logger.info("🔒 Сессия закрыта")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹ Программа завершена")