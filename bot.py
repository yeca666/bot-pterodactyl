import os
import telebot
import requests

# --- CONFIGURACIÓN ---
# Estos valores se configuran en el panel del hosting, no aquí
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
        # Limpiamos la URL por si acaso
        base_url = PTERO_URL.rstrip('/')
        url = f"{base_url}/api/client"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            servers = response.json()['data']
            markup = telebot.types.InlineKeyboardMarkup()
            
            for s in servers:
                name = s['attributes']['name']
                uuid = s['attributes']['identifier']
                # Limpiamos el nombre para que no supere los 30 caracteres y no dé error
                clean_name = (name[:30] + '..') if len(name) > 30 else name
                markup.add(telebot.types.InlineKeyboardButton(text=f"🕹️ {clean_name}", callback_query_data=f"pow_{uuid}"))
            
            bot.send_message(message.chat.id, "Selecciona un servidor para encender:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, f"❌ Error del Panel (Código: {response.status_code})")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error de conexión: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pow_'))
def handle_query(call):
    uuid = call.data.split('_')[1]
    base_url = PTERO_URL.rstrip('/')
    url = f"{base_url}/api/client/servers/{uuid}/power"
    headers = {"Authorization": f"Bearer {PTERO_KEY}"}
    
    try:
        res = requests.post(url, json={"signal": "start"}, headers=headers)
        if res.status_code in [204, 200]:
            bot.answer_callback_query(call.id, "🚀 ¡Orden enviada!")
            bot.edit_message_text(f"✅ Servidor {uuid} arrancando...", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Error al enviar")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Error de red")

if __name__ == '__main__':
    print("Bot en marcha...")
    bot.infinity_polling()
