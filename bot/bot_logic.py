from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from datetime import datetime, timedelta
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
from bot import data, indicators
import logging

logger = logging.getLogger(__name__)

# Кэш для хранения RSI значений
rsi_cache = {}

def format_rsi_message(pair, rsi_value, period):
    if rsi_value is None:
        return f"❌ Не удалось получить RSI для {pair}"
    
    if rsi_value > 70:
        status = "🔴 Перекупленность"
    elif rsi_value < 30:
        status = "🟢 Перепроданность"
    else:
        status = "🟡 Нейтрально"
    
    return f"""📈 {pair}
RSI: {rsi_value:.2f} (период {period})
{status}"""

async def get_rsi_for_pair(pair, user_id):
    """Получаем RSI с кэшированием на 1 минуту"""
    settings = get_user_settings(user_id)
    period = settings.get('rsi_period', 14)
    
    # Проверяем кэш
    if pair in rsi_cache:
        value, timestamp = rsi_cache[pair]
        if datetime.now() - timestamp < timedelta(minutes=1):
            return format_rsi_message(pair, value, period)
    
    # Получаем новые данные
    try:
        df = data.fetch_ohlcv(pair)
        rsi_value = indicators.calculate_rsi(df, period)
        rsi_cache[pair] = (rsi_value, datetime.now())
        return format_rsi_message(pair, rsi_value, period)
    except Exception as e:
        logger.error(f"Ошибка получения RSI для {pair}: {e}")
        return f"❌ Ошибка расчета RSI для {pair}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📊 Бот мониторинга RSI

Основные команды:
/rsi_all - RSI всех подписанных пар
/rsi - RSI конкретной пары (меню выбора)
/settings - текущие настройки
/set_rsi [период] - изменить период RSI
/add [пара] - добавить пару
/remove [пара] - удалить пару
/list - мои пары
/pairs - все доступные пары
/add_all - добавить все пары
/remove_all - удалить все пары

Примеры:
/set_rsi 21 - установит период 21
/add BTC/USDT - добавит пару
/rsi - покажет меню выбора пар
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

async def show_current_rsi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать RSI для всех подписанных пар"""
    user_id = update.effective_user.id
    pairs = get_pairs(user_id)
    
    if not pairs:
        await update.message.reply_text("У вас нет подписанных пар. Добавьте пары через /add")
        return
    
    message = "📊 Текущие значения RSI:\n\n"
    for pair in pairs:
        rsi_message = await get_rsi_for_pair(pair, user_id)
        message += f"{rsi_message}\n\n"
    
    await update.message.reply_text(message)

async def select_pair_for_rsi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню выбора пар"""
    user_id = update.effective_user.id
    pairs = get_pairs(user_id)
    
    if not pairs:
        await update.message.reply_text("У вас нет подписанных пар. Добавьте пары через /add")
        return
    
    keyboard = []
    for pair in pairs:
        keyboard.append([InlineKeyboardButton(pair, callback_data=f"show_rsi_{pair}")])
    
    await update.message.reply_text(
        "Выберите пару для проверки RSI:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_rsi_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("show_rsi_"):
        pair = query.data.replace("show_rsi_", "")
        user_id = query.from_user.id
        rsi_message = await get_rsi_for_pair(pair, user_id)
        
        # Добавляем кнопку обновления
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_rsi_{pair}")]
        ]
        
        await query.edit_message_text(
            rsi_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith("refresh_rsi_"):
        pair = query.data.replace("refresh_rsi_", "")
        user_id = query.from_user.id
        # Удаляем значение из кэша для принудительного обновления
        if pair in rsi_cache:
            del rsi_cache[pair]
        
        rsi_message = await get_rsi_for_pair(pair, user_id)
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_rsi_{pair}")]
        ]
        
        await query.edit_message_text(
            rsi_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

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

async def show_available_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = get_available_pairs()
    await update.message.reply_text("📌 Доступные пары:\n\n" + "\n".join(pairs))

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
    
    # Новые команды RSI
    app.add_handler(CommandHandler("rsi_all", show_current_rsi))
    app.add_handler(CommandHandler("rsi", select_pair_for_rsi))
    app.add_handler(CallbackQueryHandler(handle_rsi_button))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling()