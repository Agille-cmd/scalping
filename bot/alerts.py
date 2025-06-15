import requests
import time

def send_telegram_message(bot_token, chat_id, message, max_retries=3):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                print(f"Ошибка Telegram API (попытка {attempt + 1}): {response.text}")
        except Exception as e:
            print(f"Ошибка соединения (попытка {attempt + 1}): {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Экспоненциальная задержка
    
    return False