from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.data import TELEGRAM_TOKEN, AVAILABLE_PAIRS, AVAILABLE_INTERVALS
from bot.user_data import (
    add_pair, remove_pair, clear_pairs,
    set_rsi_period, get_rsi_period,
    get_user_pairs, set_time_interval, get_time_interval
)
from bot.indicators import get_rsi

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Клавиатура для выбора пар
def pairs_keyboard(action: str):
    builder = InlineKeyboardBuilder()
    for pair in AVAILABLE_PAIRS:
        builder.button(text=pair, callback_data=f"{action}_{pair}")
    builder.adjust(2)
    return builder.as_markup()

def intervals_keyboard():
    builder = InlineKeyboardBuilder()
    for interval in AVAILABLE_INTERVALS:
        builder.button(text=interval, callback_data=f"interval_{interval}")
    builder.adjust(2)
    return builder.as_markup()

@router.message(Command("help"))
async def help_command(msg: Message):
    help_text = (
        "🤖 *Бот мониторинга RSI*\n\n"
        "🔹 Основные команды:\n"
        "/pairs - доступные пары\n"
        "/list - ваши подписки\n"
        "/add - добавить пару (меню)\n"
        "/remove - убрать пару (меню)\n"
        "/add_all - подписаться на все\n"
        "/remove_all - очистить подписки\n"
        "/rsi [число] - изменить период\n"
        "/check - проверить текущие RSI\n\n"
        "📊 Бот автоматически уведомляет при:\n"
        "RSI > 70 (перекупленность)\n"
        "RSI < 30 (перепроданность)"
    )
    await msg.answer(help_text, parse_mode="Markdown")

@router.message(Command("add"))
async def add_menu(msg: Message):
    await msg.answer(
        "Выберите пару для добавления:",
        reply_markup=pairs_keyboard("add")
    )

@router.message(Command("remove"))
async def remove_menu(msg: Message):
    await msg.answer(
        "Выберите пару для удаления:",
        reply_markup=pairs_keyboard("remove")
    )

@router.message(Command("add_all"))
async def add_all(msg: Message):
    for pair in AVAILABLE_PAIRS:
        add_pair(msg.from_user.id, pair)
    await msg.answer("✅ Подписаны на все доступные пары")

@router.message(Command("remove_all"))
async def remove_all(msg: Message):
    clear_pairs(msg.from_user.id)
    await msg.answer("🧹 Все подписки удалены")

@router.callback_query(lambda c: c.data.startswith(("add_", "remove_")))
async def handle_pair_selection(callback: types.CallbackQuery):
    action, pair = callback.data.split('_')
    user_id = callback.from_user.id
    
    if action == "add":
        if add_pair(user_id, pair):
            await callback.answer(f"✅ {pair} добавлена")
        else:
            await callback.answer(f"❌ {pair} уже есть")
    else:
        if remove_pair(user_id, pair):
            await callback.answer(f"❌ {pair} удалена")
        else:
            await callback.answer(f"⚠️ {pair} не найдена")

    # Обновляем сообщение с кнопками
    await callback.message.edit_reply_markup(
        reply_markup=pairs_keyboard(action)
    )

@router.message(Command("rsi"))
async def set_rsi(msg: Message):
    try:
        period = int(msg.text.split()[1])
        if 1 <= period <= 100:
            set_rsi_period(msg.from_user.id, period)
            await msg.answer(f"✅ Установлен RSI период: {period}")
        else:
            await msg.answer("Период должен быть 1-100")
    except (IndexError, ValueError):
        await msg.answer("Укажите период: /rsi 14")

@router.message(Command("pairs"))
async def pairs_command(msg: Message):
    await msg.answer("📊 Доступные пары:\n" + "\n".join(AVAILABLE_PAIRS))

@router.message(Command("list"))
async def list_command(msg: Message):
    pairs = get_user_pairs(msg.from_user.id)
    await msg.answer("Ваши пары:\n" + "\n".join(pairs) if pairs else "Нет подписок")

@router.message(Command("check"))
async def check_command(msg: Message):
    pairs = get_user_pairs(msg.from_user.id)
    if not pairs:
        await msg.answer("Нет подписок")
        return
    
    await msg.answer(
        "Выберите пару для проверки:",
        reply_markup=pairs_keyboard("check")
    )

@router.callback_query(lambda c: c.data.startswith("check_"))
async def handle_check_selection(callback: types.CallbackQuery):
    pair = callback.data.split('_')[1]
    user_id = callback.from_user.id
    
    await callback.answer("Запрашиваю данные...")
    
    rsi = get_rsi(user_id, pair)
    
    if rsi is None:
        await callback.message.answer(
            "⚠️ Не удалось получить данные. Возможные причины:\n"
            "1. Лимит запросов к API (макс. 5/мин)\n"
            "2. Проблемы с интернет-соединением\n"
            "3. Временная недоступность сервиса\n\n"
            "Попробуйте позже или измените интервал (/interval)"
        )
        return
    
    period = get_rsi_period(user_id)
    interval = get_time_interval(user_id)
    status = "🔴 >70" if rsi > 70 else "🟢 <30" if rsi < 30 else "🟡"
    
    await callback.message.edit_text(
        f"📊 {pair} (интервал: {interval})\n"
        f"RSI({period}): {rsi:.2f} {status}\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardBuilder()
            .button(text="Изменить интервал", callback_data=f"change_interval_{pair}")
            .as_markup()
    )

@router.callback_query(lambda c: c.data.startswith("back_to_check_"))
async def handle_back_to_check(callback: types.CallbackQuery):
    _, _, pair = callback.data.split('_', 2)
    user_id = callback.from_user.id
    rsi = get_rsi(user_id, pair)
    
    if rsi is None:
        await callback.answer("Ошибка получения данных")
        return
    
    period = get_rsi_period(user_id)
    interval = get_time_interval(user_id)
    status = "🔴 >70" if rsi > 70 else "🟢 <30" if rsi < 30 else "🟡"
    
    await callback.message.edit_text(
        f"📊 {pair} (интервал: {interval})\n"
        f"RSI({period}): {rsi:.2f} {status}\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardBuilder()
            .button(text="Изменить интервал", callback_data=f"change_interval_{pair}")
            .as_markup()
    )

@router.message(Command("interval"))
async def interval_menu(msg: Message):
    await msg.answer(
        "Выберите интервал свечей:",
        reply_markup=intervals_keyboard()
    )

# Обработчик для изменения интервала
@router.callback_query(lambda c: c.data.startswith(("interval_", "change_interval_")))
async def handle_interval_selection(callback: types.CallbackQuery):
    try:
        if callback.data.startswith("interval_"):
            interval = callback.data.split('_')[1]
            set_time_interval(callback.from_user.id, interval)
            await callback.answer(f"✅ Интервал изменен на {interval}")
            await callback.message.delete()
        else:
            pair = callback.data.split('_')[2]
            await callback.message.edit_reply_markup(
                reply_markup=InlineKeyboardBuilder()
                    .button(text="Назад", callback_data=f"check_{pair}")
                    .as_markup()
            )
            await callback.message.answer(
                "Выберите интервал свечей:",
                reply_markup=intervals_keyboard()
            )
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}")

@router.message()
async def unknown_command(msg: Message):
    await msg.answer("Неизвестная команда. Используйте /help")