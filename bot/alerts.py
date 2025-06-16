from aiogram import Bot
from bot.data import TELEGRAM_TOKEN
from bot.user_data import user_pairs, get_rsi_period
from bot.indicators import get_rsi
import asyncio

bot = Bot(token=TELEGRAM_TOKEN)

async def check_rsi_levels():
    while True:
        for user_id, pairs in user_pairs.items():
            for pair in pairs:
                rsi = get_rsi(user_id, pair)
                if rsi is None:
                    continue
                
                period = get_rsi_period(user_id)
                if rsi > 70:
                    await bot.send_message(user_id, f"⚠️ {pair} RSI({period})={rsi:.2f} - ПЕРЕКУПЛЕННОСТЬ!")
                elif rsi < 30:
                    await bot.send_message(user_id, f"⚠️ {pair} RSI({period})={rsi:.2f} - ПЕРЕПРОДАННОСТЬ!")
        
        await asyncio.sleep(300)  # 5 минут

async def start_monitoring():
    asyncio.create_task(check_rsi_levels())