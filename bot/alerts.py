import requests
import asyncio
from datetime import datetime
from bot.data import API_PROVIDERS
from bot.indicators import get_rsi  # Импорт функции get_rsi
from bot.user_data import get_rsi_period, load_data  # Импорт функций из user_data
from bot.bot_logic import bot  # Импорт экземпляра бота

async def check_api_status():
    while True:
        for provider in API_PROVIDERS:
            if not provider.get('active', True):
                try:
                    test_url = f"{provider['url']}/status" if provider['name'] == 'twelvedata' else f"{provider['url']}/v1/marketstatus"
                    response = requests.get(test_url, timeout=5)
                    if response.status_code == 200:
                        provider['active'] = True
                        print(f"API {provider['name']} restored")
                except Exception as e:
                    print(f"API check error: {str(e)}")
        await asyncio.sleep(3600)

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
        
        await asyncio.sleep(300)  # Проверка каждые 5 минут

async def start_monitoring():
    asyncio.create_task(check_rsi_levels())