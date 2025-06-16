from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import Message
from bot.data import TELEGRAM_TOKEN, AVAILABLE_PAIRS
from bot.user_data import *
from bot.indicators import get_rsi

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
router = Router()

@dp.message(Command("help"))
async def help_command(msg: Message):
    text = (
        "🤖 *Доступные команды:*\n"
        "/help — помощь\n"
        "/check — проверить RSI ваших пар\n"
        "/pairs — доступные валютные пары\n"
        "/list — ваши подписки\n"
        "/add EUR/USD — добавить пару\n"
        "/add_all — подписаться на все пары\n"
        "/remove EUR/USD — убрать пару\n"
        "/remove_all — убрать все пары\n"
        "/rsi 10 — установить период RSI\n"
        "\nБот автоматически уведомит при RSI > 70 или < 30"
    )
    await msg.answer(text, parse_mode="Markdown")

@dp.message(Command("pairs"))
async def pairs_command(msg: Message):
    await msg.answer("📊 Доступные пары:\n" + "\n".join(AVAILABLE_PAIRS))

@dp.message(Command("list"))
async def list_command(msg: Message):
    pairs = get_user_pairs(msg.from_user.id)
    await msg.answer("Ваши пары:\n" + "\n".join(pairs) if pairs else "Нет подписок")

@dp.message(Command("add"))
async def add_command(msg: Message):
    try:
        pair = msg.text.split()[1].upper()
        if pair in AVAILABLE_PAIRS:
            add_pair(msg.from_user.id, pair)
            await msg.answer(f"✅ Добавлено: {pair}")
        else:
            await msg.answer("Неверная пара. Используйте /pairs")
    except IndexError:
        await msg.answer("Укажите пару: /add EUR/USD")

@dp.message(Command("add_all"))
async def add_all_command(msg: Message):
    for pair in AVAILABLE_PAIRS:
        add_pair(msg.from_user.id, pair)
    await msg.answer("✅ Подписаны на все пары")

@dp.message(Command("remove"))
async def remove_command(msg: Message):
    try:
        pair = msg.text.split()[1].upper()
        remove_pair(msg.from_user.id, pair)
        await msg.answer(f"❌ Удалено: {pair}")
    except IndexError:
        await msg.answer("Укажите пару: /remove EUR/USD")

@dp.message(Command("remove_all"))
async def remove_all_command(msg: Message):
    clear_pairs(msg.from_user.id)
    await msg.answer("🧹 Все пары удалены")

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