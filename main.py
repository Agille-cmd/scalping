import logging
from bot import dp, bot, start_monitoring
import asyncio
from bot.alerts import check_api_status
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    asyncio.create_task(check_api_status())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())