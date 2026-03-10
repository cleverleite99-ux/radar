import time
import os
from scrape_match import scrape_match
from telegram_notifier import send_telegram_message, get_telegram_updates
from brain import analyze_match

URLS_FILE = "urls.txt"

def load_urls():
    if not os.path.exists(URLS_FILE):
        return []
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]
    return list(set(urls))

def save_url(url):
    urls = load_urls()
    if url not in urls:
        with open(URLS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{url}\n")
        return True
    return False

def remove_url(url_to_remove):
    urls = load_urls()
    new_urls = [u for u in urls if u != url_to_remove]
    if len(new_urls) < len(urls):
        with open(URLS_FILE, "w", encoding="utf-8") as f:
            for u in new_urls:
                f.write(f"{u}\n")
        return True
    return False

def check_telegram_for_new_urls(last_update_id):
    updates = get_telegram_updates(offset=last_update_id + 1 if last_update_id else None)
    
    force_stats = False
    system_running = None # None significa sin cambio, True arranca, False para
    
    for update in updates:
        update_id = update.get("update_id")
        if last_update_id is None or update_id > last_update_id:
            last_update_id = update_id
            
        message = update.get("message", {})
        text = message.get("text", "").strip()
        
        # Procesamiento de Comandos
        if text.startswith("/start"):
            system_running = True
            send_telegram_message("▶️ <b>Sistema Iniciado:</b> Monitoreo reanudado.")
        elif text.startswith("/stop"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1 and "http" in parts[1]:
                target_url = parts[1].strip()
                if remove_url(target_url):
                    send_telegram_message(f"🗑️ <b>Partido eliminado del monitoreo</b>:\n{target_url}")
                else:
                    send_telegram_message("⚠️ No se encontró esa URL en la lista de monitoreo.")
            else:
                system_running = False
                send_telegram_message("⏸️ <b>Sistema Pausado:</b> Monitoreo general detenido.")
        elif text.startswith("/stats"):
            force_stats = True
            send_telegram_message("🔄 <b>Recopilando estadísticas ahora mismo...</b>")
            
        # Si el texto parece una URL de flashscore, la añadimos
        elif "flashscore" in text and "http" in text:
            if save_url(text):
                send_telegram_message("✅ <b>Partido añadido</b>")
                
    return last_update_id, force_stats, system_running

def format_stats_message(url, home_team, away_team, score, time_str, stats, ia_note=""):
    if not stats:
        return f"⏳ <b>Partido Pendiente o Sin Estadísticas</b>\n<b>{home_team}</b> vs <b>{away_team}</b>\n<a href='{url}'>Ver en Flashscore</a>\n(Aún no hay datos. Se volverá a intentar.)"

    msg = f"⚽ <b>¡Estadísticas Actualizadas!</b>\n"
    msg += f"<b>{home_team}</b> {score} <b>{away_team}</b>\n"
    msg += f"⏱️ <i>{time_str}</i>\n"
    msg += f"<a href='{url}'>Ver en Flashscore</a>\n\n"
    
    emoji_map = {
        'Expected goals (xG)': '⚽',
        'Ball possession': '📈',
        'Total shots': '🎯',
        'Shots on target': '🎯',
        'Big chances': '🔥',
        'Corner kicks': '🚩',
        'Fouls': '🛑',
        'Yellow cards': '🟨',
        'Red cards': '🟥'
    }
    
    seen_stats = set()
    for s in stats:
        cat = s['category']
        if cat in emoji_map and cat not in seen_stats:
            icon = emoji_map[cat]
            msg += f"{icon} <b>{cat}</b>: {s['home']} - {s['away']}\n"
            seen_stats.add(cat)
            
    if ia_note:
        msg += f"\n🤖 <b>Nota de la IA:</b>\n{ia_note}"
            
    return msg

def main():
    print("Iniciando Radar Futbol Watcher...")
    send_telegram_message("🤖 <b>Radar Futbol Iniciado</b>\nEscuchando URLs por mensaje o comandos (/start, /stop, /stats).")
    
    # Asegurarse que el archivo exista
    if not os.path.exists(URLS_FILE):
        open(URLS_FILE, 'w').close()
        
    last_update_id = None
    is_running = True
    last_scrape_time = 0
    SCRAPE_INTERVAL = 600  # 10 minutos
    
    # Bucle principal infinito
    while True:
        last_update_id, force_stats, system_status_change = check_telegram_for_new_urls(last_update_id)
        
        if system_status_change is not None:
            is_running = system_status_change
            if system_status_change:
                # Al reiniciar forzamos extracción para arrancar enseguida si ya pasó el tiempo
                last_scrape_time = 0 
                
        current_time = time.time()
        should_scrape = force_stats or (is_running and (current_time - last_scrape_time) >= SCRAPE_INTERVAL)
        
        if should_scrape:
            urls = load_urls()
            if urls:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando ronda de scraping para {len(urls)} URLs...")
                for idx, url in enumerate(urls):
                    try:
                        stats, home, away, score, match_time = scrape_match(url, f"temp_{idx}.json", headless=True)
                        ia_note = analyze_match(home, away, score, match_time, stats)
                        msg = format_stats_message(url, home, away, score, match_time, stats, ia_note)
                        
                        # Comprobar si el partido ha terminado para enviarlo por última vez y borrarlo
                        match_time_lower = match_time.lower()
                        is_finished = "finished" in match_time_lower or "finalizado" in match_time_lower or "terminado" in match_time_lower
                        
                        if is_finished:
                            msg = "🏁 <b>PARTIDO FINALIZADO</b> 🏁\n" + msg
                            
                        send_telegram_message(msg)
                        
                        if is_finished:
                            remove_url(url)
                            print(f"Partido terminado eliminado: {url}")
                            
                    except Exception as e:
                        print(f"Error procesando {url}: {e}")
            else:
                if force_stats:
                    send_telegram_message("⚠️ No hay URLs pendientes en la lista para revisar.")
                    
            last_scrape_time = current_time
            
        # Dormimos un poco para no bombardear Telegram con long-polling de getUpdates
        # getUpdates ya tiene timeout de 100 dentro de telegram_notifier.py pero por si acaso
        # evitamos la carga alta de CPU.
        time.sleep(1)

if __name__ == "__main__":
    main()
