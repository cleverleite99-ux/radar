import json
import argparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from telegram_notifier import send_telegram_message

def extract_stats_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('div', class_=lambda c: c and 'wcl-row' in c)
    
    stats_data = []
    
    for row in rows:
        # Los divs internos contienen los valores individuales
        # Ignoramos el primer div porque es el contenedor de flexbox y su texto es la concatenación de todo
        divs = row.find_all('div')
        texts = [d.text.strip() for d in divs if d.text.strip()]
        
        # Esperamos al menos 4 textos: [Concatenado, Home, Category, Away]
        if len(texts) >= 4:
            home_val = texts[1]
            stat_name = texts[2]
            away_val = texts[3]
            stats_data.append({
                "category": stat_name,
                "home": home_val,
                "away": away_val
            })

    return stats_data

def scrape_match(url, output_file, headless=True):
    print(f"Iniciando extracción para: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()
        
        # Ir a la página
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        # Intentar cerrar el banner de cookies si aparece
        try:
            # Seleccionamos el botón de aceptar cookies por su ID común en Flashscore
            accept_button = page.locator('#onetrust-accept-btn-handler')
            if accept_button.is_visible(timeout=3000):
                print("Aceptando cookies...")
                accept_button.click()
        except Exception as e:
            print("No se encontró el banner de cookies o ya estaba cerrado.")
            
        # Esperar un poco a que todo renderice
        page.wait_for_timeout(2000)
        
        # Extraer el título de la página para obtener los equipos
        # Ej: "MAZ 3-1 LEO | Mazatlan FC - Club Leon"
        page_title = page.title()
        home_team, away_team = "Local", "Visitante"
        if "|" in page_title:
            teams_part = page_title.split("|")[-1].strip()
            if "-" in teams_part:
                home_team = teams_part.split("-")[0].strip()
                away_team = teams_part.split("-")[1].strip()
                
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extraer marcador y tiempo
        match_score = ""
        match_time = ""
        details = soup.find_all('div', class_='detail')
        if len(details) >= 1:
            match_score = details[0].text.strip()
        if len(details) >= 2:
            match_time = details[1].text.strip()
            
        stats = extract_stats_from_html(html)
        
        browser.close()
        return stats, home_team, away_team, match_score, match_time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flashscore stats scraper")
    parser.add_argument("--url", default="https://www.flashscore.mobi/match/Cp7zG6DG/?t=stats", help="URL del partido")
    parser.add_argument("--out", default="stats.json", help="Archivo de salida JSON")
    parser.add_argument("--show", action="store_true", help="Mostrar el navegador")
    
    args = parser.parse_args()
    
    scrape_match(args.url, args.out, headless=not args.show)
