import asyncio
import logging
import os
import re
import requests
import whois
import socket
from aiohttp import web
import asyncio
import threading

# Веб-сервер, чтобы Render не ругался
async def handle(request):
    return web.Response(text="Бот работает!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 Веб-сервер запущен на порту {port}")
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN и ADMIN_ID должны быть установлены!")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Хранилище: {message_id: user_id}
user_message_map = {}

# Хранилище состояния поиска для админа
admin_search_state = {}

# ========== КЛАВИАТУРЫ ==========
# Для обычных пользователей
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Отправить номер", request_contact=True)],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

# Для админа (OSINT-команды)
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🕵️ Поиск по username"), KeyboardButton(text="📞 Поиск по номеру")],
        [KeyboardButton(text="🔍 Sherlock username"), KeyboardButton(text="📱 TG username")],
        [KeyboardButton(text="🌐 WHOIS домен"), KeyboardButton(text="📍 IP информация")],
        [KeyboardButton(text="📧 Проверка email"), KeyboardButton(text="📊 Статистика")]
    ],
    resize_keyboard=True
)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id == ADMIN_ID

def clean_username(username: str) -> str:
    """Очистка username от @ и пробелов"""
    username = username.strip().replace('@', '').replace(' ', '')
    return username

# ========== OSINT-ФУНКЦИИ ==========

async def tg_username_search(username: str) -> str:
    """Поиск по username в Telegram"""
    username = clean_username(username)
    
    result = []
    result.append(f"🔍 <b>Поиск по username: @{username}</b>\n")
    
    # Проверка через t.me
    tg_url = f"https://t.me/{username}"
    try:
        response = requests.get(tg_url, timeout=5, allow_redirects=True)
        
        if response.status_code == 200 and "tgme_page" in response.text:
            result.append("✅ <b>Аккаунт существует!</b>")
            
            # Парсим имя
            name_match = re.search(r'<div class="tgme_page_title".*?>(.*?)</div>', response.text)
            if name_match:
                name = name_match.group(1).strip()
                result.append(f"👤 Имя: {name}")
            
            # Парсим описание
            desc_match = re.search(r'<div class="tgme_page_description".*?>(.*?)</div>', response.text)
            if desc_match:
                desc = desc_match.group(1).strip()
                desc = re.sub(r'<.*?>', '', desc)
                result.append(f"📝 Описание: {desc[:100]}")
            
            # Определяем тип
            if 'tgme_page_extra' in response.text:
                if 'bot' in response.text.lower():
                    result.append("🤖 Тип: Бот")
                else:
                    result.append("👤 Тип: Пользователь/Канал")
            
            result.append(f"🔗 Ссылка: {tg_url}")
        else:
            result.append("❌ Аккаунт НЕ найден")
    except Exception as e:
        result.append(f"❌ Ошибка при проверке: {e}")
    
    # Дополнительные источники
    result.append("\n📊 <b>Дополнительно:</b>")
    sources = [
        ("TGStat", f"https://tgstat.ru/{username}"),
        ("Telemetr", f"https://telemetr.me/{username}")
    ]
    
    for name, url in sources:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                result.append(f"📊 {name}: {url}")
        except:
            pass
    
    return "\n".join(result)

async def sherlock_search(username: str) -> str:
    """Поиск username на разных сайтах"""
    username = clean_username(username)
    
    sites = {
        "GitHub": f"https://github.com/{username}",
        "Twitter": f"https://twitter.com/{username}",
        "Instagram": f"https://instagram.com/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
        "YouTube": f"https://youtube.com/@{username}",
        "Reddit": f"https://reddit.com/user/{username}",
        "Pinterest": f"https://pinterest.com/{username}",
        "Twitch": f"https://twitch.tv/{username}",
        "VK": f"https://vk.com/{username}",
        "Facebook": f"https://facebook.com/{username}",
        "Steam": f"https://steamcommunity.com/id/{username}",
        "Spotify": f"https://open.spotify.com/user/{username}",
    }
    
    found = []
    for name, url in sites.items():
        try:
            response = requests.get(url, timeout=3, allow_redirects=True)
            if response.status_code == 200:
                found.append(f"✅ {name}: {url}")
        except:
            pass
    
    result = [f"🔍 <b>Результаты для '{username}':</b>\n"]
    if found:
        result.extend(found[:10])
        if len(found) > 10:
            result.append(f"... и еще {len(found)-10} сайтов")
    else:
        result.append("❌ Ничего не найдено")
    
    return "\n".join(result)

async def phone_search(phone: str) -> str:
    """Поиск по номеру телефона"""
    # Очищаем номер
    phone = re.sub(r'[^0-9+]', '', phone)
    
    result = [f"🔍 <b>Поиск по номеру: {phone}</b>\n"]
    
    # Поисковые системы
    result.append("📱 <b>Поиск в интернете:</b>")
    result.append(f"🔗 Google: https://google.com/search?q={phone}")
    result.append(f"🔗 Yandex: https://yandex.ru/search/?text={phone}")
    
    # Проверка Telegram (только ссылка)
    clean_phone = phone.replace('+', '')
    result.append(f"\n📱 <b>Telegram:</b>")
    result.append(f"🔗 Поиск: https://t.me/{clean_phone}")
    
    return "\n".join(result)

async def whois_search(domain: str) -> str:
    """WHOIS информация о домене"""
    try:
        w = whois.whois(domain)
        
        result = [f"🌐 <b>WHOIS: {domain}</b>\n"]
        result.append(f"📅 Создан: {w.creation_date}")
        result.append(f"📅 Истекает: {w.expiration_date}")
        result.append(f"🏢 Регистратор: {w.registrar}")
        result.append(f"👤 Владелец: {w.name or 'Скрыто'}")
        
        if w.name_servers:
            result.append(f"\n🌍 NS-сервера: {', '.join(w.name_servers[:3])}")
        
        return "\n".join([str(x) for x in result])
    except Exception as e:
        return f"❌ Ошибка: {e}"

async def ip_info(ip: str) -> str:
    """Информация по IP-адресу"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        
        if data['status'] == 'success':
            result = [f"📍 <b>IP: {ip}</b>\n"]
            result.append(f"🌍 Страна: {data['country']}")
            result.append(f"🏙 Город: {data['city']}")
            result.append(f"🏢 Провайдер: {data['isp']}")
            result.append(f"📡 Организация: {data['org']}")
            result.append(f"🗺 Координаты: {data['lat']}, {data['lon']}")
            return "\n".join(result)
        else:
            return f"❌ Информация не найдена"
    except Exception as e:
        return f"❌ Ошибка: {e}"

async def email_check(email: str) -> str:
    """Проверка email"""
    result = [f"📧 <b>Email: {email}</b>\n"]
    
    # Проверка формата
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        result.append("✅ Формат email корректен")
    else:
        result.append("❌ Неправильный формат email")
    
    # Домен email
    domain = email.split('@')[-1]
    result.append(f"\n🌐 Домен: {domain}")
    
    # Поиск в google
    result.append(f"\n🔗 Поиск: https://google.com/search?q={email}")
    
    return "\n".join(result)

# ========== ОБРАБОТЧИКИ ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        await message.answer(
            "👋 <b>Панель администратора</b>\n"
            "Используй кнопки для OSINT-поиска\n\n"
            "📌 Чтобы ответить пользователю - просто ответь на его сообщение",
            reply_markup=admin_keyboard
        )
    else:
        await message.answer(
            "👋 Привет! Я бот для связи с администратором.\n"
            "Напиши любое сообщение - оно уйдёт админу.\n\n"
            "📱 Если хочешь поделиться номером - нажми кнопку ниже:",
            reply_markup=user_keyboard
        )
    
    # Уведомление админу о новом пользователе
    if not is_admin(user_id):
        await bot.send_message(
            ADMIN_ID,
            f"👤 <b>Новый пользователь!</b>\n"
            f"🆔 ID: {user_id}\n"
            f"📱 Username: @{message.from_user.username or 'нет'}\n"
            f"👤 Имя: {message.from_user.full_name}"
        )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "🕵️ <b>OSINT-команды для админа:</b>\n\n"
            "• <b>Поиск по username</b> - Sherlock (30+ сайтов)\n"
            "• <b>TG username</b> - поиск в Telegram\n"
            "• <b>Поиск по номеру</b> - проверка телефона\n"
            "• <b>WHOIS домен</b> - информация о домене\n"
            "• <b>IP информация</b> - геолокация и провайдер\n"
            "• <b>Проверка email</b> - проверка формата\n\n"
            "Просто нажми кнопку и введи данные!"
        )
    else:
        await message.answer(
            "📋 <b>Помощь:</b>\n"
            "• Отправь любое сообщение - оно уйдёт админу\n"
            "• Нажми кнопку 📱 чтобы поделиться номером\n"
            "• Жди ответа от администратора"
        )

@dp.message(F.contact)
async def handle_contact(message: Message):
    """Получение контакта от пользователя"""
    contact = message.contact
    user_id = message.from_user.id
    
    # Пересылаем админу
    contact_info = (
        f"📞 <b>ПОЛУЧЕН НОМЕР ТЕЛЕФОНА</b>\n\n"
        f"👤 Пользователь: @{message.from_user.username or 'нет'}\n"
        f"🆔 ID: {user_id}\n"
        f"📱 Номер: <code>{contact.phone_number}</code>\n"
        f"👤 Имя: {contact.first_name} {contact.last_name or ''}"
    )
    
    sent = await bot.send_message(ADMIN_ID, contact_info)
    user_message_map[sent.message_id] = user_id
    
    await message.answer(
        "✅ Номер отправлен администратору!",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(F.text == "ℹ️ Помощь")
async def user_help_button(message: Message):
    await cmd_help(message)

# ========== ОБРАБОТЧИКИ ДЛЯ АДМИНА (OSINT) ==========

@dp.message(F.chat.id == ADMIN_ID, F.text)
async def admin_osint_commands(message: Message):
    """Обработка нажатий на кнопки OSINT"""
    text = message.text
    user_id = message.from_user.id
    
    # Меню OSINT-поиска
    if text == "🕵️ Поиск по username":
        admin_search_state[user_id] = "sherlock"
        await message.answer(
            "🔍 <b>Поиск по username (Sherlock)</b>\n"
            "Введи username (без @):"
        )
    
    elif text == "📱 TG username":
        admin_search_state[user_id] = "tg_username"
        await message.answer(
            "📱 <b>Поиск по username в Telegram</b>\n"
            "Введи username (без @):"
        )
    
    elif text == "📞 Поиск по номеру":
        admin_search_state[user_id] = "phone"
        await message.answer(
            "📞 <b>Поиск по номеру телефона</b>\n"
            "Введи номер в формате +79123456789:"
        )
    
    elif text == "🌐 WHOIS домен":
        admin_search_state[user_id] = "whois"
        await message.answer(
            "🌐 <b>WHOIS информация</b>\n"
            "Введи домен (например: google.com):"
        )
    
    elif text == "📍 IP информация":
        admin_search_state[user_id] = "ip"
        await message.answer(
            "📍 <b>Информация по IP</b>\n"
            "Введи IP-адрес (например: 8.8.8.8):"
        )
    
    elif text == "📧 Проверка email":
        admin_search_state[user_id] = "email"
        await message.answer(
            "📧 <b>Проверка email</b>\n"
            "Введи email-адрес:"
        )
    
    elif text == "📊 Статистика":
        await message.answer(
            f"📊 <b>Статистика</b>\n\n"
            f"👥 Активных диалогов: {len(user_message_map)}\n"
            f"🆔 Ваш ID: {ADMIN_ID}\n"
            f"⏱ Статус: OSINT-бот активен"
        )

# ========== ОБРАБОТЧИК ВВОДА ДЛЯ OSINT ==========
@dp.message(F.chat.id == ADMIN_ID)
async def handle_admin_osint_input(message: Message):
    """Обработка введенных данных для OSINT"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Проверяем, не ответ ли это пользователю
    if message.reply_to_message:
        original_msg_id = message.reply_to_message.message_id
        if original_msg_id in user_message_map:
            target_user = user_message_map[original_msg_id]
            
            try:
                if message.text:
                    await bot.send_message(
                        target_user,
                        f"📝 <b>Ответ администратора:</b>\n\n{message.text}"
                    )
                elif message.photo:
                    await bot.send_photo(
                        target_user,
                        message.photo[-1].file_id,
                        caption=f"📝 <b>Ответ администратора</b>\n\n{message.caption or ''}"
                    )
                else:
                    await bot.send_message(
                        target_user,
                        "📝 <b>Ответ администратора получен</b>"
                    )
                
                await message.reply("✅ Ответ отправлен пользователю!")
                return
            except Exception as e:
                await message.reply(f"❌ Ошибка: {e}")
                return
    
    # Если админ не в режиме поиска - игнорируем
    if user_id not in admin_search_state:
        return
    
    # Получаем тип поиска
    search_type = admin_search_state[user_id]
    del admin_search_state[user_id]  # Удаляем состояние
    
    # Выполняем соответствующий поиск
    try:
        await message.answer("🔍 <b>Поиск...</b>")
        
        if search_type == "tg_username":
            result = await tg_username_search(text)
            await message.answer(result, parse_mode="HTML")
        
        elif search_type == "sherlock":
            result = await sherlock_search(text)
            await message.answer(result, parse_mode="HTML")
        
        elif search_type == "phone":
            result = await phone_search(text)
            await message.answer(result, parse_mode="HTML")
        
        elif search_type == "whois":
            result = await whois_search(text)
            await message.answer(result, parse_mode="HTML")
        
        elif search_type == "ip":
            result = await ip_info(text)
            await message.answer(result, parse_mode="HTML")
        
        elif search_type == "email":
            result = await email_check(text)
            await message.answer(result, parse_mode="HTML")
    
    except Exception as e:
        await message.answer(f"❌ Ошибка при поиске: {e}")

# ========== ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ ОТ ПОЛЬЗОВАТЕЛЕЙ ==========
@dp.message()
async def handle_user_messages(message: Message):
    """Обработка сообщений от обычных пользователей"""
    user_id = message.from_user.id
    
    # Если админ - не обрабатываем здесь (уже обработано выше)
    if is_admin(user_id):
        return
    
    try:
        # Формируем информацию о пользователе
        user_info = (
            f"📩 <b>Новое сообщение</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📱 Username: @{message.from_user.username or 'нет'}\n"
            f"👤 Имя: {message.from_user.full_name}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        )
        
        # Определяем тип сообщения
        sent = None
        if message.text:
            sent = await bot.send_message(
                ADMIN_ID,
                user_info + f"📝 <b>Текст:</b>\n{message.text}"
            )
        elif message.photo:
            sent = await bot.send_photo(
                ADMIN_ID,
                message.photo[-1].file_id,
                caption=user_info + f"📝 <b>Подпись:</b>\n{message.caption or 'без подписи'}"
            )
        elif message.video:
            sent = await bot.send_video(
                ADMIN_ID,
                message.video.file_id,
                caption=user_info + f"📝 <b>Описание:</b>\n{message.caption or 'без описания'}"
            )
        elif message.document:
            sent = await bot.send_document(
                ADMIN_ID,
                message.document.file_id,
                caption=user_info + f"📝 <b>Описание:</b>\n{message.caption or 'без описания'}"
            )
        elif message.voice:
            sent = await bot.send_voice(
                ADMIN_ID,
                message.voice.file_id,
                caption=user_info + "🎤 <b>Голосовое сообщение</b>"
            )
        else:
            sent = await bot.send_message(
                ADMIN_ID,
                user_info + "📦 <b>Другой тип сообщения</b>"
            )
        
        # Сохраняем соответствие для ответа
        if sent:
            user_message_map[sent.message_id] = user_id
        
        await message.answer("✅ Сообщение доставлено администратору!")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("❌ Произошла ошибка")

# ========== ЗАПУСК ==========
async def main():
    logger.info("🚀 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())