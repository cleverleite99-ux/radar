import json
from bs4 import BeautifulSoup

def extract_stats(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    
    # Encontrar todas las filas de estadísticas buscando wcl-row_2oCpS
    # Observación: la clase exacta es 'wcl-row_2oCpS statisticsMobi' u otros
    rows = soup.find_all('div', class_=lambda c: c and 'wcl-row' in c)
    
    stats_data = []
    
    for row in rows:
        # Extraer los tres textos de la fila: valor_local, nombre_stat, valor_visitante
        # Flashscore normalmente divide estas filas en 3 divs hijos 
        # (ej. <div class="wcl-value...">, <div class="wcl-category...">, <div class="wcl-value...">)
        texts = [div.text.strip() for div in row.find_all('div', recursive=False) if div.text.strip()]
        
        if len(texts) == 3:
            home_val, stat_name, away_val = texts
            stats_data.append({
                "category": stat_name,
                "home": home_val,
                "away": away_val
            })
        elif len(texts) == 1 and row.text.strip():
            # Intentar fallback si no tiene los 3 hijos directos pero texto existe
            pass

    return stats_data

if __name__ == "__main__":
    data = extract_stats('flashscore_page.html')
    print(json.dumps(data, indent=2, ensure_ascii=False))
