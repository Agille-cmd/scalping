from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from bot.user_data import (
    get_pairs,
    add_pair,
    remove_pair,
    get_available_pairs,
    add_all_pairs,
    remove_all_pairs,
    get_user_settings,
    update_user_settings
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📊 Бот мониторинга RSI

Основные команды:
/settings - текущие настройки
/set_rsi [период] - изменить период RSI (5-30)
/add [пара] - добавить пару
/remove [пара] - удалить пару
/list - мои пары
/pairs - все доступные пары
/add_all - добавить все пары
/remove_all - удалить все пары
"""
    await update.message.reply_text(help_text)

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    await update.message.reply_text(
        f"⚙️ Ваши настройки:\n"
        f"• Период RSI: {settings['rsi_period']}\n\n"
        f"Изменить: /set_rsi [новый период]"
    )

async def set_rsi_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Укажите период RSI (например: /set_rsi 21)")
            return
        
        period = int(context.args[0])
        if not 5 <= period <= 30:
            await update.message.reply_text("Период RSI должен быть между 5 и 30")
            return
        
        user_id = update.effective_user.id
        settings = get_user_settings(user_id)
        settings['rsi_period'] = period
        update_user_settings(user_id, settings)
        
        await update.message.reply_text(f"✅ Период RSI изменен на {period}")
    except ValueError:
        await update.message.reply_text("Некорректное значение. Введите число от 5 до 30")

async def show_available_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = get_available_pairs()
    await update.message.reply_text("📌 Доступные пары:\n\n" + "\n".join(pairs))

async def add_pair_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите пару (например: /add BTC/USDT)")
        return
    
    pair = context.args[0].upper()
    if add_pair(update.effective_user.id, pair):
        await update.message.reply_text(f"✅ Добавлена пара: {pair}")
    else:
        await update.message.reply_text(
            f"❌ Не удалось добавить пару {pair}\n"
            "Возможные причины:\n"
            "- Пара уже добавлена\n"
            "- Пара недоступна\n"
            "Список пар: /pairs"
        )

async def remove_pair_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите пару (например: /remove BTC/USDT)")
        return
    
    pair = context.args[0].upper()
    if remove_pair(update.effective_user.id, pair):
        await update.message.reply_text(f"❌ Удалена пара: {pair}")
    else:
        await update.message.reply_text(f"Пара {pair} не найдена в вашем списке")

async def list_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = get_pairs(update.effective_user.id)
    if not pairs:
        await update.message.reply_text("У вас нет добавленных пар")
    else:
        await update.message.reply_text("📋 Ваши пары:\n" + "\n".join(pairs))

async def add_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if add_all_pairs(update.effective_user.id):
        count = len(get_available_pairs())
        await update.message.reply_text(f"✅ Добавлены все {count} доступных пар")
    else:
        await update.message.reply_text("❌ Не удалось добавить пары")

async def remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Да, удалить все", callback_data="confirm_remove_all")],
        [InlineKeyboardButton("Отмена", callback_data="cancel_remove_all")]
    ]
    await update.message.reply_text(
        "⚠️ Вы уверены, что хотите удалить ВСЕ пары?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_remove_all":
        remove_all_pairs(query.from_user.id)
        await query.edit_message_text("✅ Все пары удалены")
    else:
        await query.edit_message_text("❌ Удаление отменено")

def run_bot(token):
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settings", show_settings))
    app.add_handler(CommandHandler("set_rsi", set_rsi_period))
    app.add_handler(CommandHandler("add", add_pair_handler))
    app.add_handler(CommandHandler("remove", remove_pair_handler))
    app.add_handler(CommandHandler("list", list_pairs))
    app.add_handler(CommandHandler("pairs", show_available_pairs))
    app.add_handler(CommandHandler("add_all", add_all))
    app.add_handler(CommandHandler("remove_all", remove_all))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling()