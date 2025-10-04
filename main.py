import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from datetime import datetime

# Настройки бота
BOT_TOKEN = "7727901971:AAFzAWdeOKX8ZgQWuLEMoO4a2votBeMwlEw"
ADMIN_IDS = [6422904023, 987654321]  # Замените на ID администраторов
SUPPORT_CHAT_ID = -4765445638  # ID чата для уведомлений (опционально)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище для связи пользователей и сообщений
user_messages = {}

async def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = (
        "👋 Привет! Это бот технической поддержки **Fatality Client**\n\n"
        "📝 Напишите свой вопрос, и наши администраторы скоро ответят вам!\n\n"
        "⚡ Мы постараемся помочь как можно быстрее!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Частые вопросы", callback_data="faq")],
        [InlineKeyboardButton("🔧 Техподдержка", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def chatid(update: Update, context: CallbackContext) -> None:
    """Команда для получения ID чата"""
    chat = update.effective_chat
    user = update.effective_user
    
    chat_info = (
        f"📋 **Информация о чате:**\n"
        f"🏷️ Название: {chat.title or 'Личные сообщения'}\n"
        f"🆔 Chat ID: `{chat.id}`\n"
        f"📝 Тип: {chat.type}\n"
        f"👤 Ваш ID: `{user.id}`"
    )
    
    await update.message.reply_text(chat_info, parse_mode='Markdown')

async def button_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "faq":
        faq_text = (
            "❓ **Частые вопросы:**\n\n"
            "• **Проблема с установкой** - Переустановите лаунчер\n"
            "• **Клиент не запускается** - Проверьте наличие Java\n"
            "• **Вылетает игра** - Обновите видеодрайверы\n"
            "• **Не работает мод** - Переустановите клиент\n\n"
            "Если вашей проблемы нет в списке - напишите нам!"
        )
        await query.edit_message_text(faq_text, parse_mode='Markdown')
    
    elif query.data == "support":
        support_text = "💬 Напишите ваш вопрос прямо в этот чат, и администратор ответит вам!"
        await query.edit_message_text(support_text)

async def handle_user_message(update: Update, context: CallbackContext) -> None:
    """Обработчик сообщений от пользователей"""
    user_id = update.effective_user.id
    message = update.message
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    # Игнорируем команды
    if message.text and message.text.startswith('/'):
        return
    
    # Создаем клавиатуру для ответа
    reply_keyboard = [
        [
            InlineKeyboardButton("📨 Ответить", callback_data=f"reply_{user_id}"),
            InlineKeyboardButton("👀 Просмотрено", callback_data=f"viewed_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    
    # Формируем сообщение для администратора
    admin_message = (
        f"🆕 **Новое обращение**\n"
        f"👤 Пользователь: {first_name} (@{username if username else 'нет'})\n"
        f"🆔 ID: {user_id}\n"
        f"⏰ Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}\n"
        f"📝 Сообщение:\n{message.text if message.text else '📎 Медиа-файл'}"
    )
    
    # Сохраняем информацию о сообщении
    user_messages[user_id] = {
        'username': username,
        'first_name': first_name,
        'last_message': message.message_id
    }
    
    # Отправляем сообщение всем администраторам
    for admin_id in ADMIN_IDS:
        try:
            if message.text:
                sent_msg = await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                # Для медиа-файлов
                if message.photo:
                    sent_msg = await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=message.photo[-1].file_id,
                        caption=admin_message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                elif message.document:
                    sent_msg = await context.bot.send_document(
                        chat_id=admin_id,
                        document=message.document.file_id,
                        caption=admin_message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
            
            # Сохраняем ID сообщения для ответа
            if 'reply_messages' not in context.chat_data:
                context.chat_data['reply_messages'] = {}
            context.chat_data['reply_messages'][sent_msg.message_id] = user_id
            
        except Exception as e:
            logger.error(f"Ошибка отправки администратору {admin_id}: {e}")
    
    # Отправляем уведомление в группу поддержки (если указана)
    if SUPPORT_CHAT_ID:
        try:
            if message.text:
                await context.bot.send_message(
                    chat_id=SUPPORT_CHAT_ID,
                    text=admin_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                if message.photo:
                    await context.bot.send_photo(
                        chat_id=SUPPORT_CHAT_ID,
                        photo=message.photo[-1].file_id,
                        caption=admin_message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                elif message.document:
                    await context.bot.send_document(
                        chat_id=SUPPORT_CHAT_ID,
                        document=message.document.file_id,
                        caption=admin_message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
        except Exception as e:
            logger.error(f"Ошибка отправки в группу поддержки: {e}")
    
    # Подтверждение пользователю
    await message.reply_text(
        "✅ Ваше сообщение отправлено администраторам! Ожидайте ответа.",
        reply_to_message_id=message.message_id
    )

async def admin_reply_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик ответов администраторов"""
    query = update.callback_query
    data = query.data
    
    if data.startswith('reply_'):
        user_id = int(data.split('_')[1])
        context.user_data['replying_to'] = user_id
        await query.edit_message_text(
            f"💬 Введите ответ для пользователя {user_id}:"
        )
    
    elif data.startswith('viewed_'):
        user_id = int(data.split('_')[1])
        await query.edit_message_text(
            f"✅ Обращение от {user_id} отмечено как просмотренное"
        )

async def handle_admin_reply(update: Update, context: CallbackContext) -> None:
    """Обработчик текстовых ответов администраторов"""
    user_id = update.effective_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS:
        return
    
    # Проверяем, отвечает ли администратор пользователю
    if 'replying_to' in context.user_data:
        target_user_id = context.user_data['replying_to']
        admin_message = update.message.text
        
        try:
            # Отправляем ответ пользователю
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"📨 **Ответ от поддержки:**\n\n{admin_message}"
            )
            
            # Уведомляем администратора
            await update.message.reply_text("✅ Ответ отправлен пользователю!")
            
            # Очищаем состояние
            del context.user_data['replying_to']
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка отправки: {e}")
            logger.error(f"Ошибка отправки пользователю {target_user_id}: {e}")

async def broadcast_command(update: Update, context: CallbackContext) -> None:
    """Команда для рассылки сообщений (только для администраторов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для этой команды")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /broadcast <сообщение>")
        return
    
    message = ' '.join(context.args)
    await update.message.reply_text("🔄 Начинаю рассылку...")
    
    # Здесь можно добавить логику рассылки всем пользователям
    # Для этого нужно хранить ID всех пользователей, которые писали боту

async def stats_command(update: Update, context: CallbackContext) -> None:
    """Команда для статистики (только для администраторов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для этой команды")
        return
    
    stats_text = (
        f"📊 **Статистика бота:**\n"
        f"👥 Уникальных пользователей: {len(user_messages)}\n"
        f"🕒 Время работы: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chatid", chatid))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(faq|support)$"))
    application.add_handler(CallbackQueryHandler(admin_reply_handler, pattern="^(reply|viewed)_"))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_user_message))
    application.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_IDS), handle_admin_reply))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()