from aiogram import Bot
from bot.data import TELEGRAM_TOKEN
from bot.user_data import get_user_pairs, get_rsi_period
from bot.indicators import get_rsi
import asyncio

bot = Bot(token=TELEGRAM_TOKEN)

async def check_rsi_levels():
    while True:
        from bot.user_data import load_data
        data = load_data()
        
        for user_id_str, pairs in data["pairs"].items():
            user_id = int(user_id_str)
            for pair in pairs:
                rsi = get_rsi(user_id, pair)
                if rsi is None:
                    continue
                
                period = get_rsi_period(user_id)
                if rsi > 70:
                    await bot.send_message(
                        user_id, 
                        f"⚠️ *{pair}* RSI({period}) = {rsi:.2f} - ПЕРЕКУПЛЕННОСТЬ!",
                        parse_mode="Markdown"
                    )
                elif rsi < 30:
                    await bot.send_message(
                        user_id,
                        f"⚠️ *{pair}* RSI({period}) = {rsi:.2f} - ПЕРЕПРОДАННОСТЬ!",
                        parse_mode="Markdown"
                    )
        
        await asyncio.sleep(300)  # Проверка каждые 5 минут

async def start_monitoring():
    asyncio.create_task(check_rsi_levels())