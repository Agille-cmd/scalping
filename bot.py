from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from config import ALLOWED_PAIRS, TELEGRAM_TOKEN
from signals import check_signal
import asyncio
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Клавиатура для выбора валютной пары
def get_pair_keyboard(prefix: str = "signal_") -> InlineKeyboardMarkup:
    buttons = []
    for i in range(0, len(ALLOWED_PAIRS), 2):
        row = [
            InlineKeyboardButton(ALLOWED_PAIRS[i], callback_data=f"{prefix}{ALLOWED_PAIRS[i]}"),
            InlineKeyboardButton(ALLOWED_PAIRS[i+1], callback_data=f"{prefix}{ALLOWED_PAIRS[i+1]}") if i+1 < len(ALLOWED_PAIRS) else None
        ]
        buttons.append([btn for btn in row if btn])
    return InlineKeyboardMarkup(buttons)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("📊 Получить сигнал", callback_data="manual_signal")],
        [InlineKeyboardButton("🤖 Автосигналы", callback_data="auto_signals")]
    ]
    await update.message.reply_text(
        "⚡️ Бот для скальпинга бинарных опционов\n"
        "Выберите режим работы:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обработчик кнопки "Автосигналы"
async def auto_signals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.edit_message_text(
        "Выберите валютную пару для автосигналов:",
        reply_markup=get_pair_keyboard("auto_")
    )

# Обработчик ручного запроса сигнала
async def manual_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.edit_message_text(
        "Выберите валютную пару для анализа:",
        reply_markup=get_pair_keyboard()
    )

# Отправка сигнала
async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    pair = query.data.split("_")[1]
    
    await query.answer(f"Анализирую {pair}...")
    signal = check_signal(pair)
    
    if signal:
        text = (
            f"📊 *{pair}*\n"
            f"🔹 Сигнал: *{signal['signal']}*\n"
            f"🔹 Уверенность: *{signal['confidence']}%*\n"
            f"🔹 Экспирация: *2 минуты*"
        )
    else:
        text = f"❌ Сейчас нет сигнала для *{pair}*."
    
    await query.edit_message_text(text, parse_mode="Markdown")

# Запуск бота
def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(auto_signals, pattern="^auto_signals$"))
    app.add_handler(CallbackQueryHandler(manual_signal, pattern="^manual_signal$"))
    app.add_handler(CallbackQueryHandler(send_signal, pattern="^(signal|auto)_"))
    
    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()