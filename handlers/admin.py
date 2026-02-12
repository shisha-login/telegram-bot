from aiogram import F, Router
from aiogram.types import Message
import logging
from config import config
from handlers.user import user_message_map

router = Router()
logger = logging.getLogger(__name__)

# Фильтр только для админа
router.message.filter(F.chat.id == config.ADMIN_ID)

@router.message(F.reply_to_message)
async def handle_admin_reply(message: Message):
    """Обработчик ответов от админа на пересланные сообщения"""
    try:
        original_message_id = message.reply_to_message.message_id
        
        # Проверяем, есть ли информация о пользователе
        if original_message_id in user_message_map:
            user_data = user_message_map[original_message_id]
            user_id = user_data['user_id']
            
            # Определяем тип ответа
            if message.text:
                await message.bot.send_message(
                    user_id,
                    f"📝 Ответ от администратора:\n\n{message.text}"
                )
                reply_type = "текст"
                
            elif message.photo:
                caption = message.caption or "📝 Ответ от администратора"
                await message.bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=caption
                )
                reply_type = "фото"
                
            elif message.video:
                caption = message.caption or "📝 Ответ от администратора"
                await message.bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=caption
                )
                reply_type = "видео"
                
            elif message.document:
                caption = message.caption or "📝 Ответ от администратора"
                await message.bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=caption
                )
                reply_type = "документ"
                
            elif message.voice:
                await message.bot.send_voice(
                    user_id,
                    message.voice.file_id,
                    caption="📝 Ответ от администратора"
                )
                reply_type = "голосовое"
                
            elif message.audio:
                caption = message.caption or "📝 Ответ от администратора"
                await message.bot.send_audio(
                    user_id,
                    message.audio.file_id,
                    caption=caption
                )
                reply_type = "аудио"
                
            elif message.sticker:
                await message.bot.send_message(
                    user_id,
                    "📝 Ответ от администратора:"
                )
                await message.bot.send_sticker(user_id, message.sticker.file_id)
                reply_type = "стикер"
                
            elif message.animation:
                caption = message.caption or "📝 Ответ от администратора"
                await message.bot.send_animation(
                    user_id,
                    message.animation.file_id,
                    caption=caption
                )
                reply_type = "GIF"
                
            else:
                await message.bot.send_message(
                    user_id,
                    "📝 Ответ от администратора получен, но тип сообщения не поддерживается."
                )
                reply_type = "неподдерживаемый"
            
            # Подтверждение админу
            username_info = f" (@{user_data['username']})" if user_data.get('username') else ""
            await message.reply(
                f"✅ Ответ отправлен пользователю {user_data['full_name']}{username_info}\n"
                f"🆔 ID: {user_id}\n"
                f"📨 Тип ответа: {reply_type}"
            )
            
            logger.info(f"Админ ответил пользователю {user_id}. Тип ответа: {reply_type}")
            
        else:
            await message.reply(
                "❌ Не удалось найти информацию об отправителе.\n"
                "Возможно, бот был перезапущен или сообщение слишком старое."
            )
            
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа админа: {e}", exc_info=True)
        await message.reply("❌ Произошла ошибка при отправке ответа.")

@router.message()
async def handle_admin_message(message: Message):
    """Обработчик сообщений от админа не в ответ на сообщение"""
    if not message.reply_to_message:
        await message.reply(
            "ℹ️ Чтобы ответить пользователю, используйте функцию 'Ответить'\n"
            "(Reply) на пересланном сообщении.\n\n"
            "Если вы хотите отправить новое сообщение всем пользователям, "
            "эта функция пока не реализована."
        )