import asyncio
import logging
from threading import Thread
from telegram.ext import Application
from bot import bot_logic, user_data, indicators, data

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8189844575:AAFX5CUov29I-mokX6pGAn2DUi_7uGLh7EY"
CHECK_INTERVAL = 300  # 5 минут

class RSIMonitor:
    def __init__(self, app):
        self.app = app
        self._running = False

    async def check_rsi_levels(self):
        while self._running:
            try:
                all_data = user_data.load_data()
                user_pairs = all_data.get("pairs", {})
                
                for user_id_str, pairs in user_pairs.items():
                    settings = user_data.get_user_settings(int(user_id_str))
                    period = settings.get("rsi_period", 14)
                    
                    for pair in pairs:
                        try:
                            df = data.fetch_ohlcv(pair)
                            if df is not None:
                                rsi_value = indicators.calculate_rsi(df, period)
                                if rsi_value is not None:
                                    if rsi_value < 30:
                                        await self.send_alert(
                                            int(user_id_str),
                                            f"🔻 {pair} RSI({period}) = {rsi_value:.2f} (перепроданность)"
                                        )
                                    elif rsi_value > 70:
                                        await self.send_alert(
                                            int(user_id_str),
                                            f"🔺 {pair} RSI({period}) = {rsi_value:.2f} (перекупленность)"
                                        )
                        except Exception as e:
                            logger.error(f"Ошибка проверки {pair}: {e}")
                            
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
            
            await asyncio.sleep(CHECK_INTERVAL)

    async def send_alert(self, chat_id, message):
        try:
            await self.app.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")

    def start(self):
        self._running = True
        Thread(target=lambda: asyncio.run(self.check_rsi_levels()), daemon=True).start()

    def stop(self):
        self._running = False

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Инициализация бота
    bot_logic.run_bot(BOT_TOKEN)
    
    # Запуск мониторинга RSI
    monitor = RSIMonitor(application)
    monitor.start()
    
    logger.info("Бот запущен и мониторит RSI...")
    application.run_polling()
    monitor.stop()

if __name__ == '__main__':
    main()