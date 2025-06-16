from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.data import TELEGRAM_TOKEN, AVAILABLE_PAIRS
from bot.user_data import *
from bot.indicators import get_rsi

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Клавиатура для выбора пар
def pairs_keyboard(action: str):
    builder = InlineKeyboardBuilder()
    for pair in AVAILABLE_PAIRS:
        builder.button(text=pair, callback_data=f"{action}_{pair}")
    builder.adjust(2)
    return builder.as_markup()

@dp.message(Command("help"))
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

@dp.message(Command("add"))
async def add_menu(msg: Message):
    await msg.answer(
        "Выберите пару для добавления:",
        reply_markup=pairs_keyboard("add")
    )

@dp.message(Command("remove"))
async def remove_menu(msg: Message):
    await msg.answer(
        "Выберите пару для удаления:",
        reply_markup=pairs_keyboard("remove")
    )

@dp.message(Command("add_all"))
async def add_all(msg: Message):
    for pair in AVAILABLE_PAIRS:
        add_pair(msg.from_user.id, pair)
    await msg.answer("✅ Подписаны на все доступные пары")

@dp.message(Command("remove_all"))
async def remove_all(msg: Message):
    clear_pairs(msg.from_user.id)
    await msg.answer("🧹 Все подписки удалены")

@dp.callback_query(lambda c: c.data.startswith(("add_", "remove_")))
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

@dp.message(Command("rsi"))
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

@dp.message(Command("pairs"))
async def pairs_command(msg: Message):
    await msg.answer("📊 Доступные пары:\n" + "\n".join(AVAILABLE_PAIRS))

@dp.message(Command("list"))
async def list_command(msg: Message):
    pairs = get_user_pairs(msg.from_user.id)
    await msg.answer("Ваши пары:\n" + "\n".join(pairs) if pairs else "Нет подписок")

@dp.message(Command("check"))
async def check_command(msg: Message):
    pairs = get_user_pairs(msg.from_user.id)
    if not pairs:
        await msg.answer("Нет подписок")
        return
    
    results = []
    for pair in pairs:
        rsi = get_rsi(msg.from_user.id, pair)
        status = "🔴 >70" if rsi > 70 else "🟢 <30" if rsi < 30 else "🟡"
        results.append(f"{pair}: {rsi:.2f} {status}")
    
    await msg.answer("\n".join(results))

@dp.message()
async def unknown_command(msg: Message):
    await msg.answer("Неизвестная команда. Используйте /help")