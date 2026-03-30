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

# --- НАСТРОЙКИ (Берем из настроек Railway) ---
TOKEN = os.getenv("8693389808:AAEWNdONwm209Ev_TRYJjLDhfebXYVG7tPs")
ADMIN_ID = os.getenv("6431820823")

# Состояния
SELECT_PRODUCT, WAIT_FOR_TAG = range(2)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

MAIN_KEYBOARD = ReplyKeyboardMarkup([["🛒 Товары", "ℹ️ О нас", "⭐ Отзывы"]], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 *Магазин Brawl Pass Shop запущен!*\n\nВыбери нужный раздел:",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD
    )
    return SELECT_PRODUCT


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ BrawlPass — 650 руб", callback_data="buy_bp")],
        [InlineKeyboardButton("💎 BrawlPass+ — 900 руб", callback_data="buy_bpp")]
    ])
    await update.message.reply_text("🛒 *Выберите товар:*", parse_mode="Markdown", reply_markup=keyboard)
    return SELECT_PRODUCT


async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = "BrawlPass ⚡" if query.data == "buy_bp" else "BrawlPass+ 💎"
    context.user_data["product"] = product

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Купить", callback_data="confirm"),
         InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])
    await query.edit_message_text(
        f"🛍 Вы выбрали: *{product}*\nПодтвердить заказ?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return SELECT_PRODUCT


async def ask_for_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎉 Напишите ваш *игровой тег* (#ABC12345):", parse_mode="Markdown")
    return WAIT_FOR_TAG


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tag = update.message.text
    product = context.user_data.get("product", "Неизвестно")
    user = update.effective_user

    # Отправка админу
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📦 *НОВЫЙ ЗАКАЗ!*\n\nТовар: {product}\nКлиент: @{user.username}\nID: `{user.id}`\nТег: `{tag}`",
        parse_mode="Markdown"
    )

    await update.message.reply_text("✅ Заявка принята! Менеджер свяжется с вами.", reply_markup=MAIN_KEYBOARD)
    return SELECT_PRODUCT


def main():
    # На Railway прокси НЕ НУЖНЫ
    if not TOKEN or not ADMIN_ID:
        print("❌ Ошибка: Переменные BOT_TOKEN или ADMIN_ID не установлены!")
        return

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_PRODUCT: [
                MessageHandler(filters.Regex("^🛒 Товары$"), show_products),
                CallbackQueryHandler(product_selected, pattern="^buy_"),
                CallbackQueryHandler(ask_for_tag, pattern="^confirm"),
                CallbackQueryHandler(lambda u, c: SELECT_PRODUCT, pattern="^cancel"),
                MessageHandler(filters.Regex("^ℹ️ О нас$"),
                               lambda u, c: u.message.reply_text("Мы — лучший магазин по Brawl Stars!")),
                MessageHandler(filters.Regex("^⭐ Отзывы$"),
                               lambda u, c: u.message.reply_text("Отзывы скоро появятся здесь."))
            ],
            WAIT_FOR_TAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_order)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    print("🚀 Бот успешно запущен на сервере!")
    app.run_polling()


if __name__ == "__main__":
    main()
