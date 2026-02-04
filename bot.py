import os
import telebot
import requests
from threading import Thread
from flask import Flask

# Servidor para Render (Mantiene el estado Live)
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# Configuración desde Variables de Entorno
TOKEN = os.getenv("TOKEN_TELEGRAM")
PTERO_URL = os.getenv("PTERO_URL").rstrip('/')
PTERO_KEY = os.getenv("PTERO_API_KEY")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎮 Conectando con el panel...")
    headers = {"Authorization": f"Bearer {PTERO_KEY}", "Accept": "application/json"}
    
    try:
        url = f"{PTERO_URL}/api/client"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            servers = response.json()['data']
            markup = telebot.types.InlineKeyboardMarkup()
            
            for s in servers:
                name_raw = s['attributes']['name']
                uuid = s['attributes']['identifier']
                
                # LIMPIEZA EXTREMA: Solo letras y números, máximo 12 caracteres
                # Esto evita que los paréntesis de tus servers rompan Telegram
                clean_name = ''.join(char for char in name_raw if char.isalnum())[:12]
                
                markup.add(telebot.types.InlineKeyboardButton(
                    text=f"▶️ {clean_name}", 
                    callback_query_data=f"pow_{uuid}"
                ))
            
            bot.send_message(message.chat.id, "Selecciona servidor:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, f"❌ Error Panel: {response.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Error de conexión.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pow_'))
def handle_query(call):
    uuid = call.data.split('_')[1]
    url = f"{PTERO_URL}/api/client/servers/{uuid}/power"
    headers = {"Authorization": f"Bearer {PTERO_KEY}", "Content-Type": "application/json"}
    
    try:
        res = requests.post(url, json={"signal": "start"}, headers=headers)
        if res.status_code in [204, 200]:
            bot.answer_callback_query(call.id, "🚀 ¡En marcha!")
            bot.edit_message_text("✅ Encendido enviado.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ No se pudo encender.")
    except:
        bot.answer_callback_query(call.id, "❌ Error de red.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    bot.infinity_polling()
