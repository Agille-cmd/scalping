import asyncio
from bot.indicators import get_rsi
from bot.user_data import get_rsi_period, load_data
from bot.bot_logic import bot

async def check_rsi_levels():
    while True:
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

        await asyncio.sleep(180)  # Проверка каждые 3 минуты

async def start_monitoring():
    asyncio.create_task(check_rsi_levels())