import os
import telebot
import requests
from threading import Thread
from flask import Flask

# --- MINI SERVIDOR PARA RENDER (Mantiene el estado "Live") ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    # Render asigna el puerto automáticamente
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
    headers = {
        "Authorization": f"Bearer {PTERO_KEY}",
        "Accept": "application/json"
    }
    
    try:
        base_url = PTERO_URL.rstrip('/')
        url = f"{base_url}/api/client"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            servers = response.json()['data']
            markup = telebot.types.InlineKeyboardMarkup()
            
            if not servers:
                bot.send_message(message.chat.id, "No se encontraron servidores en tu cuenta.")
                return

            for s in servers:
                name = s['attributes']['name']
                uuid = s['attributes']['identifier']
                
                # --- LIMPIEZA TOTAL PARA EVITAR ERROR 400 ---
                # Quitamos símbolos raros y cortamos a 20 caracteres
                clean_name = ''.join(e for e in name if e.isalnum() or e in [' ', '-', '_'])
                display_name = (clean_name[:20] + '..') if len(clean_name) > 20 else clean_name
                if not display_name.strip(): display_name = "Servidor" # Por si el nombre era puro emoji
                
                markup.add(telebot.types.InlineKeyboardButton(
                    text=f"🕹️ {display_name}", 
                    callback_query_data=f"pow_{uuid}"
                ))
            
            bot.send_message(message.chat.id, "Selecciona un servidor para encender:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, f"❌ Error Panel: {response.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error de conexión: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pow_'))
def handle_query(call):
    uuid = call.data.split('_')[1]
    base_url = PTERO_URL.rstrip('/')
    url = f"{base_url}/api/client/servers/{uuid}/power"
    headers = {
        "Authorization": f"Bearer {PTERO_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        # Enviamos la señal de START
        res = requests.post(url, json={"signal": "start"}, headers=headers)
        if res.status_code in [204, 200]:
            bot.answer_callback_query(call.id, "🚀 ¡Orden enviada!")
            bot.edit_message_text("✅ Orden de encendido enviada al servidor!", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, f"❌ Error: {res.status_code}")
    except:
        bot.answer_callback_query(call.id, "❌ Error de red")

if __name__ == '__main__':
    # Hilo para Flask (Render Port)
    Thread(target=run_flask).start()
    print("Bot en marcha y puerto 8080 abierto...")
    # Polling infinito
    bot.infinity_polling()
