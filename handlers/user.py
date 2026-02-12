from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime
import logging
from config import config

router = Router()
logger = logging.getLogger(__name__)

# Словарь для хранения соответствия между сообщениями админа и пользователями
user_message_map = {}

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "👋 Привет! Я бот для связи с администратором.\n"
        "Напишите любое сообщение, и оно будет доставлено админу."
    )
    logger.info(f"Пользователь {message.from_user.id} (@{message.from_user.username}) запустил бота")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📋 Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Показать эту справку\n\n"
        "Просто отправьте любое сообщение, и администратор получит его."
    )

@router.message(F.chat.type == "private")
async def handle_user_message(message: Message):
    """Обработчик сообщений от обычных пользователей"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        full_name = message.from_user.full_name
        
        # Формируем служебную информацию
        user_info = []
        user_info.append(f"🆔 ID: {user_id}")
        user_info.append(f"📱 Username: @{username}" if username else "📱 Username: отсутствует")
        user_info.append(f"👤 Имя: {full_name}")
        
        # Добавляем информацию о времени
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        user_info.append(f"⏰ Время: {current_time}")
        
        # Добавляем информацию о чате
        if message.chat.username:
            user_info.append(f"💬 Чат: @{message.chat.username}")
        
        user_info_text = "\n".join(user_info)
        
        # Определяем тип сообщения и отправляем админу
        sent_message = None
        message_type = "текст"
        
        if message.text:
            sent_message = await message.bot.send_message(
                config.ADMIN_ID,
                f"📩 Новое сообщение:\n\n{user_info_text}\n\n📝 Текст:\n{message.text}"
            )
            
        elif message.photo:
            message_type = "фото"
            caption = message.caption or "без подписи"
            sent_message = await message.bot.send_photo(
                config.ADMIN_ID,
                message.photo[-1].file_id,
                caption=f"📩 Новое фото:\n\n{user_info_text}\n\n📝 Подпись:\n{caption}"
            )
            
        elif message.video:
            message_type = "видео"
            caption = message.caption or "без подписи"
            sent_message = await message.bot.send_video(
                config.ADMIN_ID,
                message.video.file_id,
                caption=f"📩 Новое видео:\n\n{user_info_text}\n\n📝 Подпись:\n{caption}"
            )
            
        elif message.document:
            message_type = "документ"
            caption = message.caption or "без подписи"
            sent_message = await message.bot.send_document(
                config.ADMIN_ID,
                message.document.file_id,
                caption=f"📩 Новый документ:\n\n{user_info_text}\n\n📝 Подпись:\n{caption}"
            )
            
        elif message.voice:
            message_type = "голосовое"
            sent_message = await message.bot.send_voice(
                config.ADMIN_ID,
                message.voice.file_id,
                caption=f"📩 Новое голосовое сообщение:\n\n{user_info_text}"
            )
            
        elif message.audio:
            message_type = "аудио"
            caption = message.caption or "без подписи"
            sent_message = await message.bot.send_audio(
                config.ADMIN_ID,
                message.audio.file_id,
                caption=f"📩 Новая аудиозапись:\n\n{user_info_text}\n\n📝 Подпись:\n{caption}"
            )
            
        elif message.sticker:
            message_type = "стикер"
            sent_message = await message.bot.send_message(
                config.ADMIN_ID,
                f"📩 Новый стикер:\n\n{user_info_text}"
            )
            await message.bot.send_sticker(config.ADMIN_ID, message.sticker.file_id)
            
        elif message.animation:
            message_type = "GIF"
            caption = message.caption or "без подписи"
            sent_message = await message.bot.send_animation(
                config.ADMIN_ID,
                message.animation.file_id,
                caption=f"📩 Новая анимация:\n\n{user_info_text}\n\n📝 Подпись:\n{caption}"
            )
            
        elif message.contact:
            message_type = "контакт"
            contact = message.contact
            contact_info = f"Имя: {contact.first_name} {contact.last_name or ''}\nТелефон: {contact.phone_number}"
            if contact.user_id:
                contact_info += f"\nUser ID: {contact.user_id}"
            sent_message = await message.bot.send_message(
                config.ADMIN_ID,
                f"📩 Новый контакт:\n\n{user_info_text}\n\n📇 Данные контакта:\n{contact_info}"
            )
            
        elif message.location:
            message_type = "геолокация"
            loc = message.location
            maps_link = f"https://www.google.com/maps?q={loc.latitude},{loc.longitude}"
            sent_message = await message.bot.send_message(
                config.ADMIN_ID,
                f"📩 Новая геолокация:\n\n{user_info_text}\n\n📍 Координаты:\n"
                f"Широта: {loc.latitude}\nДолгота: {loc.longitude}\n"
                f"🗺 Карта: {maps_link}"
            )
            
        else:
            sent_message = await message.bot.send_message(
                config.ADMIN_ID,
                f"📩 Новое сообщение (неподдерживаемый тип):\n\n{user_info_text}"
            )
        
        # Сохраняем соответствие для ответа
        if sent_message:
            user_message_map[sent_message.message_id] = {
                'user_id': user_id,
                'username': username,
                'full_name': full_name,
                'message_type': message_type,
                'timestamp': current_time
            }
        
        # Отправляем подтверждение пользователю
        await message.answer("✅ Ваше сообщение доставлено администратору. Ожидайте ответа.")
        logger.info(f"Сообщение от {user_id} (@{username}) переслано админу. Тип: {message_type}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от {message.from_user.id}: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при отправке сообщения. Попробуйте позже.")