import os
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# --- НАСТРОЙКИ (Берем из Railway) ---
TOKEN = os.getenv("8693389808:AAEWNdONwm209Ev_TRYJjLDhfebXYVG7tPs")
# Теперь можно вписать ID через запятую в Railway, например: 12345,67890
ADMIN_STR = os.getenv("6431820823", "")
ADMIN_IDS = [int(i.strip()) for i in ADMIN_STR.split(",") if i.strip().isdigit()]

# Состояния
SELECT_PRODUCT, WAIT_FOR_ID = range(2)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Главное меню
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["🛒 Товары", "ℹ️ О нас"], ["⭐ Отзывы"]], 
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Привет, боец!*\n\nТы попал в самый надежный магазин *Brawl Pass Shop*! 🌵\n"
        "Здесь ты можешь быстро и безопасно прокачать свой аккаунт.\n\n"
        "👇 Выбирай раздел в меню:", 
        parse_mode="Markdown", 
        reply_markup=MAIN_KEYBOARD
    )
    return SELECT_PRODUCT

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Brawl Pass — 650₽", callback_data="buy_bp")],
        [InlineKeyboardButton("💎 Brawl Pass Plus — 900₽", callback_data="buy_bpp")]
    ])
    await update.message.reply_text("🛒 *Доступные товары:*", parse_mode="Markdown", reply_markup=keyboard)
    return SELECT_PRODUCT

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product = "Brawl Pass ⚡" if query.data == "buy_bp" else "Brawl Pass Plus 💎"
    context.user_data["product"] = product
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Оформить", callback_data="confirm"),
         InlineKeyboardButton("❌ Назад", callback_data="cancel")]
    ])
    await query.edit_message_text(
        f"🛍 Вы выбрали: *{product}*\n\nЖелаете перейти к оплате и вводу данных?", 
        parse_mode="Markdown", 
        reply_markup=keyboard
    )
    return SELECT_PRODUCT

async def ask_for_supercell_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📧 *Почти готово!*\n\nНапишите ваш *Supercell ID* (например: `SuperStar11@gmail.com` или никнейм ID).\n"
        "⚠️ Убедитесь, что данные верны, чтобы менеджер нашел ваш аккаунт!", 
        parse_mode="Markdown"
    )
    return WAIT_FOR_ID

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_val = update.message.text
    product = context.user_data.get("product", "Неизвестно")
    user = update.effective_user
    
    order_text = (
        f"🔔 *НОВЫЙ ЗАКАЗ!*\n\n"
        f"📦 Товар: *{product}*\n"
        f"👤 Клиент: @{user.username if user.username else 'Скрыт'}\n"
        f"🆔 ID пользователя: `{user.id}`\n"
        f"🎮 Supercell ID: `{user_id_val}`"
    )

    # Рассылка всем админам из списка
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin, text=order_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить админу {admin}: {e}")
    
    await update.message.reply_text(
        "✅ *Заявка успешно создана!*\n\nМенеджер проверит данные и напишет вам в личные сообщения для завершения оплаты. Спасибо за выбор! 🚀", 
        parse_mode="Markdown", 
        reply_markup=MAIN_KEYBOARD
    )
    return SELECT_PRODUCT

async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "ℹ️ *О нашем магазине:*\n\n"
        "🌟 Мы работаем на рынке более 2-х лет!\n"
        "✅ Выполнено более *5000+* успешных заказов.\n"
        "⚡ Мгновенная доставка после оплаты.\n"
        "🔒 Гарантируем безопасность вашего аккаунта — вход только по коду!\n\n"
        "👑 Наша цель — сделать донат в Brawl Stars доступным для каждого игрока в РФ и СНГ!"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")
    return SELECT_PRODUCT

async def reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Читать отзывы", url="https://t.me/ВАША_ССЫЛКА_НА_ОТЗЫВЫ")]
    ])
    await update.message.reply_text(
        "⭐ *Наши отзывы:*\n\nМы дорожим своей репутацией! Посмотрите, что о нас пишут другие игроки:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return SELECT_PRODUCT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Заказ отменен. Вы можете выбрать другой товар.")
    return SELECT_PRODUCT

def main():
    if not TOKEN or not ADMIN_IDS:
        print("❌ Ошибка: Укажите BOT_TOKEN и ADMIN_ID в настройках Railway!")
        return

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_PRODUCT: [
                MessageHandler(filters.Regex("^🛒 Товары$"), show_products),
                MessageHandler(filters.Regex("^ℹ️ О нас$"), about_us),
                MessageHandler(filters.Regex("^⭐ Отзывы$"), reviews),
                CallbackQueryHandler(product_selected, pattern="^buy_"),
                CallbackQueryHandler(ask_for_supercell_id, pattern="^confirm"),
                CallbackQueryHandler(cancel, pattern="^cancel"),
            ],
            WAIT_FOR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_order)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    print(f"🚀 Бот запущен! Список админов: {ADMIN_IDS}")
    app.run_polling()

if __name__ == "__main__":
    main()
