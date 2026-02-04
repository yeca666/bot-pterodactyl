import os
import telebot
import requests
from threading import Thread
from flask import Flask

# --- MINI SERVIDOR PARA RENDER ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    # Render usa la variable PORT, si no existe usa el 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURACIÓN DEL BOT ---
TOKEN = os.getenv("TOKEN_TELEGRAM")
PTERO_URL = os.getenv("PTERO_URL")
PTERO_KEY = os.getenv("PTERO_API_KEY")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎮 Conectando con el panel Xeon...")
    headers = {"Authorization": f"Bearer {PTERO_KEY}", "Accept": "application/json"}
    
    try:
        base_url = PTERO_URL.rstrip('/')
        url = f"{base_url}/api/client"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            servers = response.json()['data']
            markup = telebot.types.InlineKeyboardMarkup()
            
            for s in servers:
                name = s['attributes']['name']
                uuid = s['attributes']['identifier']
                # Limitamos el nombre a 20 caracteres para evitar errores de Telegram
                clean_name = (name[:20] + '..') if len(name) > 20 else name
                markup.add(telebot.types.InlineKeyboardButton(text=f"🕹️ {clean_name}", callback_query_data=f"pow_{uuid}"))
            
            bot.send_message(message.chat.id, "Selecciona un servidor:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, f"❌ Error Panel: {response.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# (El resto del código de power_handler se queda igual...)

if __name__ == '__main__':
    # Arrancamos el mini-servidor en un hilo aparte
    Thread(target=run_flask).start()
    print("Bot en marcha...")
    bot.infinity_polling()
