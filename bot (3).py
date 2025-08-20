import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler
)
import json
import os
import random
from datetime import datetime
import matplotlib.pyplot as plt
import io

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
(
    SET_BALANCE, MAIN_MENU, TRADE_JOURNAL, NEW_TRADE_EMOTION, 
    NEW_TRADE_STRATEGY, TRADE_TYPE, CHECK_EXTREMUM, CHECK_ZONE, 
    CHECK_BREAKOUT, CHECK_CONFIRMATION, TRADE_CONFIRMATION, 
    TRADE_RESULT, TRADE_DIRECTION, CHECK_FIBONACCI
) = range(14)

# Прогрессивные уровни риска
RISK_LEVELS = [
    (0, 150, 0.05),
    (150, 350, 0.04),
    (350, 1000, 0.03),
    (1000, 5000, 0.02),
    (5000, float('inf'), 0.01)
]

# Мотивационные сообщения (улучшенные)
WIN_MOTIVATION = [
    "🎯 Блестяще! Ты только что заработал ${profit:.2f}!",
    "🚀 Космическая прибыль! +${profit:.2f} к балансу!",
    "🏆 Идеальный вход! Твой винрейт: {win_rate:.1f}%",
    "💸 Прибыль как по учебнику! {motivation_quote}",
    "💰 Финансовый снайпер! Баланс: ${balance:.2f}"
]

LOSS_MOTIVATION = [
    "🛡️ Не сдавайся! ${loss:.2f} - это просто ступенька к успеху",
    "🌧️ Временная неудача. Твой винрейт: {win_rate:.1f}%",
    "🔥 Ценный урок! Помни: '{motivation_quote}'",
    "🚧 Всего одна сделка из многих. Баланс: ${balance:.2f}",
    "🌱 Каждая потеря ${loss:.2f} - семя будущей победы"
]

GENERAL_MOTIVATION = [
    "💡 Успешная торговля — это 20% стратегия и 80% психология",
    "🧠 Дисциплина важнее, чем предсказание рынка",
    "⚖️ Рискуй только тем, что готов потерять",
    "📈 Тренд — твой лучший друг",
    "🔍 Анализируй, планируй, исполняй"
]

# Визуальные примеры (ссылки на изображения)
VISUAL_EXAMPLES = {
    "swing_low": "https://fsr-develop.ru/wp-content/uploads/2023/09/image-1322-1024x722.png",
    "swing_high": "https://fsr-develop.ru/wp-content/uploads/2023/09/image-1322-1024x722.png",
    "liquidity_pool_long": "https://blog.opofinance.com/en/wp-content/uploads/2024/09/Mastering-ICT-Liquidity-Trading-4.jpg",
    "liquidity_pool_short": "https://blog.opofinance.com/en/wp-content/uploads/2024/09/Mastering-ICT-Liquidity-Trading-4.jpg",
    "breakout_long": "https://blog.opofinance.com/en/wp-content/uploads/2024/10/Breakout-Trading-Strategy-3.jpg",
    "breakout_short": "https://blog.opofinance.com/en/wp-content/uploads/2024/10/Breakout-Trading-Strategy-3.jpg",
    "fibonacci": "https://www.tradingsim.com/hubfs/Fibretracement-jpeg.png",
    "risk_management": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTE9zIipV9qsOcZdo8_vwmGmeqsziQn7jyonQ&s",
    "confirmation_long": "https://blog.opofinance.com/en/wp-content/uploads/2024/09/Mastering-ICT-Liquidity-Trading-4.jpg",
    "confirmation_short": "https://blog.opofinance.com/en/wp-content/uploads/2024/09/Mastering-ICT-Liquidity-Trading-4.jpg"
}

# Функции для работы с данными
def load_user_data(user_id: int) -> dict:
    filename = f"user_{user_id}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {"balance": None, "trades": []}

def save_user_data(user_id: int, data: dict):
    filename = f"user_{user_id}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_position_size(balance: float) -> float:
    for min_bal, max_bal, risk_percent in RISK_LEVELS:
        if min_bal <= balance < max_bal:
            return balance * risk_percent
    return balance * 0.01

def get_enhanced_motivation(user_data: dict, m_type: str) -> str:
    trades = user_data.get('trades', [])
    balance = user_data.get('balance', 0)
    win_rate = 0
    
    if trades:
        profit_count = sum(1 for t in trades if t.get('profit', 0) > 0)
        win_rate = (profit_count / len(trades)) * 100
        
        if m_type == "win" and trades:
            last_profit = trades[-1].get('profit', 0)
            msg = random.choice(WIN_MOTIVATION)
            return msg.format(
                profit=last_profit,
                win_rate=win_rate,
                balance=balance,
                motivation_quote=random.choice(GENERAL_MOTIVATION)
            )
        elif m_type == "loss" and trades:
            last_loss = abs(trades[-1].get('profit', 0))
            msg = random.choice(LOSS_MOTIVATION)
            return msg.format(
                loss=last_loss,
                win_rate=win_rate,
                balance=balance,
                motivation_quote=random.choice(GENERAL_MOTIVATION)
            )
    
    return random.choice(GENERAL_MOTIVATION)

def generate_balance_chart(user_data: dict):
    """Генерирует график баланса"""
    trades = user_data.get('trades', [])
    if len(trades) < 2:
        return None
        
    # Собираем данные для графика
    balances = []
    dates = []
    for trade in trades:
        if 'balance_after' in trade and 'exit_time' in trade:
            balances.append(trade['balance_after'])
            dates.append(trade['exit_time'])
    
    if len(balances) < 2:
        return None
    
    # Создаем график
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(balances)), balances, marker='o', linestyle='-', color='#4CAF50', linewidth=2, markersize=6)
    plt.title('📈 История баланса', fontsize=14, pad=20)
    plt.xlabel('Номер сделки', fontsize=12)
    plt.ylabel('Баланс ($)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Сохраняем в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=80)
    buf.seek(0)
    plt.close()
    return buf

# Обработчики команд
def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info(f"Пользователь {user.first_name} запустил бота")
    
    user_data = load_user_data(user.id)
    context.user_data['user_data'] = user_data
    
    if user_data.get('balance') is None:
        reply_keyboard = [['💰 Установить баланс']]
        update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\n"
            "Я твой личный трейдинг-помощник.\n\n"
            "💰 Для начала установи свой стартовый депозит:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return SET_BALANCE
    
    return show_main_menu(update, context)

def set_balance(update: Update, context: CallbackContext) -> int:
    if update.message.text == '💰 Установить баланс':
        update.message.reply_text(
            "Введи сумму стартового депозита (в USD):",
            reply_markup=ReplyKeyboardRemove()
        )
        return SET_BALANCE
    
    try:
        balance = float(update.message.text)
        if balance <= 0:
            raise ValueError
    except ValueError:
        update.message.reply_text(
            "❌ Нужно число больше нуля. Введи сумму депозита:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SET_BALANCE
    
    user_id = update.message.from_user.id
    user_data = context.user_data['user_data']
    user_data['balance'] = balance
    save_user_data(user_id, user_data)
    
    reply_keyboard = [['🏠 Главное меню']]
    update.message.reply_text(
        f"✅ Отлично! Стартовый баланс: ${balance:.2f}\n\n"
        f"{get_enhanced_motivation(user_data, 'general')}",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return MAIN_MENU

def show_main_menu(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data['user_data']
    balance = user_data['balance']
    position_size = calculate_position_size(balance)
    
    reply_keyboard = [
        ['🎯 Новая сделка', '📊 История сделок'],
        ['💰 Мой баланс', '💡 Мотивация']
    ]
    
    text = (
        f"💼 Твой баланс: ${balance:.2f}\n"
        f"🎯 Рекомендуемый размер позиции: ${position_size:.2f}\n\n"
        "Выбери действие:"
    )
    
    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)
    )
    return MAIN_MENU

def show_journal(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data['user_data']
    trades = user_data['trades']
    
    if not trades:
        reply_keyboard = [['🏠 Главное меню']]
        update.message.reply_text(
            "📭 У тебя еще нет сделок\n\n"
            f"{get_enhanced_motivation(user_data, 'general')}",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return MAIN_MENU
    
    # Генерируем график баланса
    chart = generate_balance_chart(user_data)
    
    text = "📋 Последние сделки:\n\n"
    for i, trade in enumerate(trades[-5:], 1):
        result = "✅ Прибыль" if trade.get('profit', 0) > 0 else "❌ Убыток"
        text += (
            f"{i}. {trade.get('symbol', 'N/A')} - {trade.get('trade_type', 'N/A')}\n"
            f"   Результат: {result} ${abs(trade.get('profit', 0)):.2f}\n"
            f"   Дата: {trade.get('exit_time', 'N/A')}\n\n"
        )
    
    profit_count = sum(1 for t in trades if t.get('profit', 0) > 0)
    loss_count = len(trades) - profit_count
    win_rate = (profit_count / len(trades)) * 100 if trades else 0
    
    text += (
        f"📈 Статистика:\n"
        f"   Всего сделок: {len(trades)}\n"
        f"   Прибыльных: {profit_count} | Убыточных: {loss_count}\n"
        f"   Успешность: {win_rate:.1f}%\n\n"
    )
    
    if win_rate > 60:
        text += f"⭐ Отличные результаты!\n{get_enhanced_motivation(user_data, 'win')}"
    elif win_rate < 40:
        text += f"💪 Продолжай работать!\n{get_enhanced_motivation(user_data, 'loss')}"
    else:
        text += get_enhanced_motivation(user_data, 'general')
    
    reply_keyboard = [['🏠 Главное меню']]
    
    if chart:
        update.message.reply_photo(
            photo=chart, 
            caption=text,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    else:
        update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    return MAIN_MENU

def new_trade_start(update: Update, context: CallbackContext) -> int:
    # Определяем текущую торговую сессию
    now_utc = datetime.utcnow()
    hour = now_utc.hour
    session_info = ""
    
    if 0 <= hour < 6:  # Азиатская сессия
        session_info = "🌏 Сейчас азиатская сессия - обычно низкая волатильность"
    elif 6 <= hour < 12:  # Европейская сессия
        session_info = "🌍 Сейчас европейская сессия - волатильность нарастает"
    elif 12 <= hour < 18:  # Американская сессия
        session_info = "🌎 Сейчас американская сессия - высокая волатильность!"
    else:  # Вечерняя сессия
        session_info = "🌙 Вечерняя сессия - волатильность снижается"
    
    reply_keyboard = [
        ['😊 Спокоен', '😐 Нейтрален'], 
        ['😰 Взволнован', '😡 Эмоционален'],
        ['🏠 Главное меню']
    ]
    
    update.message.reply_text(
        f"🧠 ШАГ 1 из 8: Твое состояние\n\n"
        f"{session_info}\n\n"
        "Как ты себя чувствуешь перед сделкой?\n\n"
        "📌 Совет: Если ты взволнован или эмоционален, лучше отложи торговлю.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return NEW_TRADE_EMOTION

def handle_emotion(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    emotion = update.message.text
    context.user_data['current_trade'] = {"emotion": emotion}
    
    reply_keyboard = [['✅ Да, все проверено', '❌ Нет, есть сомнения'], ['🔙 Назад', '🏠 Главное меню']]
    update.message.reply_text(
        "📋 ШАГ 2 из 8: Проверка плана\n\n"
        "Проверил ли ты эти ключевые моменты?\n\n"
        "1. 📊 Определен ли тренд на старшем таймфрейме?\n"
        "2. 💧 Видна ли ближайшая зона ликвидности?\n" 
        "3. ⚠️ Поставлен ли стоп-лосс?\n\n"
        "Все ли готово для сделки?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return NEW_TRADE_STRATEGY

def handle_strategy(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        return new_trade_start(update, context)
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    if '❌ Нет' in update.message.text:
        reply_keyboard = [['🏠 Главное меню']]
        update.message.reply_text(
            "⛔ Стоит остановиться!\n\n"
            "Лучше подготовиться:\n"
            "• 📝 Проверить анализ\n"
            "• ⏳ Дождаться сигналов\n\n"
            f"{get_enhanced_motivation(context.user_data['user_data'], 'loss')}",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return MAIN_MENU
    
    reply_keyboard = [['🔙 Назад', '🏠 Главное меню']]
    update.message.reply_text(
        "📌 В какой паре планируешь сделку?\n(Например: BTCUSDT или EURUSD)",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return TRADE_TYPE

def handle_symbol(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        return handle_emotion(update, context)
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    symbol = update.message.text.upper()
    context.user_data['current_trade']['symbol'] = symbol
    
    reply_keyboard = [['📈 Лонг', '📉 Шорт'], ['🔙 Назад', '🏠 Главное меню']]
    update.message.reply_text(
        "📊 Какое направление выбираешь?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return TRADE_DIRECTION

def handle_trade_type(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        reply_keyboard = [['🔙 Назад', '🏠 Главное меню']]
        update.message.reply_text(
            "📌 В какой паре планируешь сделку?\n(Например: BTCUSDT или EURUSD)",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return TRADE_TYPE
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    trade_type = 'Лонг' if '📈' in update.message.text else 'Шорт'
    context.user_data['current_trade']['trade_type'] = trade_type
    
    if trade_type == 'Лонг':
        reply_keyboard = [['✅ Да, вижу минимум', '❌ Не вижу минимума'], ['🔙 Назад', '🏠 Главное меню']]
        update.message.reply_text(
            "📍 ШАГ 3 из 8: Поиск минимума\n\n"
            "Видишь четкий минимум (дно), от которого цена отскочила?\n\n"
            "Нашел хороший уровень для входа в лонг?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    else:
        reply_keyboard = [['✅ Да, вижу максимум', '❌ Не вижу максимума'], ['🔙 Назад', '🏠 Главное меню']]
        update.message.reply_text(
            "📍 ШАГ 3 из 8: Поиск максимума\n\n"
            "Видишь четкий максимум (вершину), от которого цена отскочила?\n\n"
            "Нашел хороший уровень для входа в шорт?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    return CHECK_EXTREMUM

def check_extremum(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        reply_keyboard = [['📈 Лонг', '📉 Шорт'], ['🔙 Назад', '🏠 Главное меню']]
        update.message.reply_text(
            "📊 Какое направление выбираешь?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return TRADE_DIRECTION
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    if '❌ Не вижу' in update.message.text:
        reply_keyboard = [['🏠 Главное меню']]
        update.message.reply_text(
            "❌ Стоит подождать!\n\n"
            "Лучше дождаться четкого уровня:\n"
            "• ⏳ Ждать формирования экстремума\n"
            "• 📊 Перейти на старший таймфрейм\n\n"
            f"{get_enhanced_motivation(context.user_data['user_data'], 'loss')}",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return MAIN_MENU
    
    trade_type = context.user_data['current_trade']['trade_type']
    
    # Переходим к вопросу о зоне ликвидности
    if trade_type == 'Лонг':
        reply_keyboard = [['✅ Да, вижу зону', '❌ Нет, не вижу'], ['🔙 Назад', '🏠 Главное меню']]
        update.message.reply_text(
            "💧 ШАГ 4 из 8: Зона ликвидности\n\n"
            "Ищешь область НИЖЕ минимума, где могут быть стоп-лоссы?\n\n"
            "Нашел зону ликвидности?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    else:
        reply_keyboard = [['✅ Да, вижу зону', '❌ Нет, не вижу'], ['🔙 Назад', '🏠 Главное меню']]
        update.message.reply_text(
            "💧 ШАГ 4 из 8: Зона ликвидности\n\n"
            "Ищешь область ВЫШЕ максимума, где могут быть стоп-лоссы?\n\n"
            "Нашел зону ликвидности?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    return CHECK_ZONE

def check_zone(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        trade_type = context.user_data['current_trade']['trade_type']
        if trade_type == 'Лонг':
            reply_keyboard = [['✅ Да, вижу минимум', '❌ Не вижу минимума'], ['🔙 Назад', '🏠 Главное меню']]
            update.message.reply_text(
                "📍 ШАГ 3 из 8: Поиск минимума\n\n"
                "Видишь четкий минимум (дно), от которого цена отскочила?\n\n"
                "Нашел хороший уровень для входа в лонг?",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
        else:
            reply_keyboard = [['✅ Да, вижу максимум', '❌ Не вижу максимума'], ['🔙 Назад', '🏠 Главное меню']]
            update.message.reply_text(
                "📍 ШАГ 3 из 8: Поиск максимума\n\n"
                "Видишь четкий максимум (вершину), от которого цена отскочила?\n\n"
                "Нашел хороший уровень для входа в шорт?",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
        return CHECK_EXTREMUM
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    if '❌ Нет' in update.message.text:
        reply_keyboard = [['🏠 Главное меню']]
        update.message.reply_text(
            "⚠️ Нужно найти зону!\n\n"
            "Что делать:\n"
            "• 🔍 Перепроверить график\n"
            "• 📊 Проверить на старшем таймфрейме\n\n"
            f"{get_enhanced_motivation(context.user_data['user_data'], 'loss')}",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return MAIN_MENU
    
    # Добавляем вопрос про пробой ликвидности
    trade_type = context.user_data['current_trade']['trade_type']
    
    reply_keyboard = [['✅ Да, был пробой', '❌ Нет, не было'], ['🔙 Назад', '🏠 Главное меню']]
    update.message.reply_text(
        f"💥 ШАГ 5 из 8: Пробой ликвидности\n\n"
        f"Цена пробила зону ликвидности и быстро вернулась?\n\n"
        "Был ли такой пробой?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CHECK_BREAKOUT

def check_breakout(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        trade_type = context.user_data['current_trade']['trade_type']
        reply_keyboard = [['✅ Да, вижу зону', '❌ Нет, не вижу'], ['🔙 Назад', '🏠 Главное меню']]
        if trade_type == 'Лонг':
            update.message.reply_text(
                "💧 ШАГ 4 из 8: Зона ликвидности\n\n"
                "Нашел область ВЫШЕ минимума, где могут быть стоп-лоссы?\n\n"
                "Нашел зону ликвидности?",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
        else:
            update.message.reply_text(
                "💧 ШАГ 4 из 8: Зона ликвидности\n\n"
                "Нашел область НИЖЕ максимума, где могут быть стоп-лоссы?\n\n"
                "Нашел зону ликвидности?",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
        return CHECK_ZONE
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    if '❌ Нет' in update.message.text:
        reply_keyboard = [['🏠 Главное меню']]
        update.message.reply_text(
            "⏳ Нужно дождаться пробоя!\n\n"
            "Что делать:\n"
            "• 👀 Наблюдать за зоной\n"
            "• ⛔ Не входить без пробоя\n\n"
            f"{get_enhanced_motivation(context.user_data['user_data'], 'general')}",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return MAIN_MENU
    
    trade_type = context.user_data['current_trade']['trade_type']
    
    reply_keyboard = [['✅ Да, есть подтверждение', '❌ Нет, нет подтверждения'], ['🔙 Назад', '🏠 Главное меню']]
    update.message.reply_text(
        "🔄 ШАГ 6 из 8: Подтверждение отскока\n\n"
        f"Цена отскочила от уровня и пошла в нужном направлении?\n\n"
        "Есть подтверждение?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CHECK_CONFIRMATION

def check_confirmation(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        trade_type = context.user_data['current_trade']['trade_type']
        reply_keyboard = [['✅ Да, был пробой', '❌ Нет, не было'], ['🔙 Назад', '🏠 Главное меню']]
        update.message.reply_text(
            f"💥 ШАГ 5 из 8: Пробой ликвидности\n\n"
            f"Цена пробила зону ликвидности и быстро вернулась?\n\n"
            "Был ли такой пробой?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return CHECK_BREAKOUT
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    answer = update.message.text
    trade_type = context.user_data['current_trade']['trade_type']
    
    if '❌ Нет' in answer:
        reply_keyboard = [['🏠 Главное меню']]
        update.message.reply_text(
            "✋ Опасно! Нет подтверждения\n\n"
            "Рекомендация:\n"
            "• ⏳ Ждать четкого сигнала\n"
            "• 🔍 Искать другие возможности\n\n"
            f"{get_enhanced_motivation(context.user_data['user_data'], 'loss')}",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return MAIN_MENU
    
    # Расчет размера позиции
    user_data = context.user_data['user_data']
    balance = user_data['balance']
    position_size = calculate_position_size(balance)
    
    context.user_data['current_trade']['size'] = position_size
    context.user_data['current_trade']['entry_time'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    reply_keyboard = [['✅ Подтверждаю вход', '❌ Отменить сделку'], ['🔙 Назад', '🏠 Главное меню']]
    update.message.reply_text(
        f"🎉 ШАГ 7 из 8: Подтверждение сделки!\n\n"
        f"📊 Все условия выполнены для входа в {trade_type}!\n\n"
        f"💵 Размер позиции: ${position_size:.2f}\n"
        f"📈 Это {position_size/balance*100:.1f}% от баланса\n\n"
        "Подтверждаешь вход?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return TRADE_CONFIRMATION

def handle_trade_confirmation(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        trade_type = context.user_data['current_trade']['trade_type']
        reply_keyboard = [['✅ Да, есть подтверждение', '❌ Нет, нет подтверждения'], ['🔙 Назад', '🏠 Главное меню']]
        update.message.reply_text(
            "🔄 ШАГ 6 из 8: Подтверждение отскока\n\n"
            f"Цена отскочила от уровня и пошла в нужном направлении?\n\n"
            "Есть подтверждение?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return CHECK_CONFIRMATION
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    if "❌" in update.message.text:
        reply_keyboard = [['🏠 Главное меню']]
        update.message.reply_text(
            "🚫 Сделка отменена\n\n"
            f"{get_enhanced_motivation(context.user_data['user_data'], 'general')}",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return MAIN_MENU
    
    # Сохраняем данные о сделке перед входом
    current_trade = context.user_data['current_trade']
    current_trade['status'] = 'open'
    current_trade['balance_before'] = context.user_data['user_data']['balance']
    
    user_data = context.user_data['user_data']
    user_data['trades'].append(current_trade)
    save_user_data(update.message.from_user.id, user_data)
    
    reply_keyboard = [['✅ Сделка в плюсе', '❌ Сделка в минусе'], ['🔙 Назад', '🏠 Главное меню']]
    update.message.reply_text(
        "📌 Сделка открыта! Жду результата...\n\n"
        "Как закроешь сделку, сообщи результат:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return TRADE_RESULT

def handle_trade_result(update: Update, context: CallbackContext) -> int:
    if update.message.text == '🔙 Назад':
        reply_keyboard = [['✅ Подтверждаю вход', '❌ Отменить сделку'], ['🔙 Назад', '🏠 Главное меню']]
        trade_type = context.user_data['current_trade']['trade_type']
        user_data = context.user_data['user_data']
        balance = user_data['balance']
        position_size = calculate_position_size(balance)
        
        update.message.reply_text(
            f"🎉 ШАГ 7 из 8: Подтверждение сделки!\n\n"
            f"📊 Все условия выполнены для входа в {trade_type}!\n\n"
            f"💵 Размер позиции: ${position_size:.2f}\n"
            f"📈 Это {position_size/balance*100:.1f}% от баланса\n\n"
            "Подтверждаешь вход?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return TRADE_CONFIRMATION
    elif update.message.text == '🏠 Главное меню':
        return show_main_menu(update, context)
        
    user_id = update.message.from_user.id
    user_data = context.user_data['user_data']
    
    # Находим последнюю открытую сделку
    open_trades = [t for t in user_data['trades'] if t.get('status') == 'open']
    if not open_trades:
        update.message.reply_text("⚠️ Не найдено открытых сделок")
        return show_main_menu(update, context)
    
    current_trade = open_trades[-1]
    position_size = current_trade['size']
    
    # Рассчитываем результат
    is_profitable = "✅" in update.message.text
    profit = position_size * 0.8 if is_profitable else -position_size
    
    # Обновляем баланс
    new_balance = user_data['balance'] + profit
    user_data['balance'] = new_balance
    
    # Обновляем данные о сделке
    current_trade.update({
        'status': 'closed',
        'profit': profit,
        'balance_after': new_balance,
        'exit_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'result': 'profit' if is_profitable else 'loss'
    })
    
    save_user_data(user_id, user_data)
    
    # Формируем отчет
    result_text = (
        f"📊 Отчет о сделке:\n\n"
        f"Результат: {'✅ Прибыль' if is_profitable else '❌ Убыток'}\n"
        f"Сумма: ${abs(profit):.2f} {'+' if is_profitable else ''}\n"
        f"Размер позиции: ${position_size:.2f}\n"
        f"Новый баланс: ${new_balance:.2f}\n\n"
    )
    
    # Добавляем персонализированную мотивацию
    if is_profitable:
        result_text += f"⭐ {get_enhanced_motivation(user_data, 'win')}\n\n"
    else:
        result_text += f"💪 {get_enhanced_motivation(user_data, 'loss')}\n\n"
    
    # Рассчет нового размера позиции
    new_position_size = calculate_position_size(new_balance)
    result_text += (
        f"🔍 Для следующей сделки:\n"
        f"Рекомендуемый размер позиции: ${new_position_size:.2f}\n"
        f"Это {new_position_size/new_balance*100:.1f}% от баланса"
    )
    
    reply_keyboard = [['🏠 Главное меню']]
    update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return MAIN_MENU

def show_motivation(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['🏠 Главное меню']]
    update.message.reply_text(
        f"💡 Мотивация для тебя:\n\n{get_enhanced_motivation(context.user_data['user_data'], 'general')}",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return MAIN_MENU

def show_balance(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data['user_data']
    balance = user_data['balance']
    position_size = calculate_position_size(balance)
    
    reply_keyboard = [['🏠 Главное меню']]
    update.message.reply_text(
        f"💰 Твой баланс: ${balance:.2f}\n"
        f"🎯 Рекомендуемый размер позиции: ${position_size:.2f}\n\n"
        f"💡 {get_enhanced_motivation(user_data, 'general')}",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return MAIN_MENU

def cancel(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['🏠 Главное меню']]
    update.message.reply_text(
        'Действие отменено',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return show_main_menu(update, context)

def main() -> None:
    TOKEN = "7422938992:AAGJ_Z2wuuGE1OrzI23ln3kTD46vAUASIoI"  # Замените на свой токен
    
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SET_BALANCE: [MessageHandler(Filters.text & ~Filters.command, set_balance)],
            MAIN_MENU: [
                MessageHandler(Filters.regex('^🎯 Новая сделка$'), new_trade_start),
                MessageHandler(Filters.regex('^📊 История сделок$'), show_journal),
                MessageHandler(Filters.regex('^💰 Мой баланс$'), show_balance),
                MessageHandler(Filters.regex('^💡 Мотивация$'), show_motivation),
                MessageHandler(Filters.regex('^🏠 Главное меню$'), show_main_menu)
            ],
            NEW_TRADE_EMOTION: [
                MessageHandler(Filters.regex(r'^(😊 Спокоен|😐 Нейтрален|😰 Взволнован|😡 Эмоционален|🏠 Главное меню)$'), handle_emotion)
            ],
            NEW_TRADE_STRATEGY: [
                MessageHandler(Filters.regex(r'^(✅ Да, все проверено|❌ Нет, есть сомнения|🔙 Назад|🏠 Главное меню)$'), handle_strategy)
            ],
            TRADE_TYPE: [
                MessageHandler(Filters.text & ~Filters.command, handle_symbol),
                MessageHandler(Filters.regex('^(🔙 Назад|🏠 Главное меню)$'), handle_emotion)
            ],
            TRADE_DIRECTION: [
                MessageHandler(Filters.regex(r'^(📈 Лонг|📉 Шорт|🔙 Назад|🏠 Главное меню)$'), handle_trade_type)
            ],
            CHECK_EXTREMUM: [
                MessageHandler(Filters.regex(r'^(✅ Да, вижу минимум|✅ Да, вижу максимум|❌ Не вижу минимума|❌ Не вижу максимума|🔙 Назад|🏠 Главное меню)$'), check_extremum)
            ],
            CHECK_ZONE: [
                MessageHandler(Filters.regex(r'^(✅ Да, вижу зону|❌ Нет, не вижу|🔙 Назад|🏠 Главное меню)$'), check_zone)
            ],
            CHECK_BREAKOUT: [
                MessageHandler(Filters.regex(r'^(✅ Да, был пробой|❌ Нет, не было|🔙 Назад|🏠 Главное меню)$'), check_breakout)
            ],
            CHECK_CONFIRMATION: [
                MessageHandler(Filters.regex(r'^(✅ Да, есть подтверждение|❌ Нет, нет подтверждения|🔙 Назад|🏠 Главное меню)$'), check_confirmation)
            ],
            TRADE_CONFIRMATION: [
                MessageHandler(Filters.regex(r'^(✅ Подтверждаю вход|❌ Отменить сделку|🔙 Назад|🏠 Главное меню)$'), handle_trade_confirmation)
            ],
            TRADE_RESULT: [
                MessageHandler(Filters.regex(r'^(✅ Сделка в плюсе|❌ Сделка в минусе|🔙 Назад|🏠 Главное меню)$'), handle_trade_result)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()