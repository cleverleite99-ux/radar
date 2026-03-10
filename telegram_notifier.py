import requests
import sys

# Credenciales del bot y usuario de Telegram
BOT_TOKEN = "8655342684:AAHleEshaRcHIN-YjfQcf_SxdySZVzX9uLg"
CHAT_ID = "1132391254"

def send_telegram_message(message):
    """
    Envía un mensaje de texto a Telegram utilizando la API HTTPS (requests).
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Mensaje enviado con éxito a Telegram.")
        return True
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
        print("Respuesta de Telegram:", response.text)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)
        
    return False

def get_telegram_updates(offset=None):
    """
    Obtiene los últimos mensajes enviados al bot para leer URLs.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 100}
    if offset:
        params["offset"] = offset
        
    try:
        response = requests.get(url, params=params, timeout=110)
        response.raise_for_status()
        return response.json().get("result", [])
    except Exception as e:
        print("Error obteniendo actualizaciones de Telegram:", e)
    
    return []

if __name__ == "__main__":
    # Si se pasa un mensaje por línea de comandos, enviarlo, sino un mensaje por defecto
    msg = sys.argv[1] if len(sys.argv) > 1 else 'Hola, sistema listo'
    send_telegram_message(msg)
