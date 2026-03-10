import json

def load_predictions(json_path="plantillasheets.json"):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def normalize_text(text):
    return text.lower().replace("fc", "").replace("club", "").strip()

def find_match_prediction(home_team, away_team, predictions):
    h_norm = normalize_text(home_team)
    a_norm = normalize_text(away_team)
    
    for match in predictions:
        pred_h = normalize_text(match.get("HOME", ""))
        pred_a = normalize_text(match.get("AWAY", ""))
        
        # Coincidencia parcial simple
        if (h_norm in pred_h or pred_h in h_norm) and (a_norm in pred_a or pred_a in a_norm):
            return match
            
    return None

def analyze_match(home_team, away_team, score, match_time, stats):
    """
    Compara las estadísticas en vivo con la previsión base.
    Retorna un string con la nota de la IA si hay algo destacable.
    """
    predictions = load_predictions()
    match_data = find_match_prediction(home_team, away_team, predictions)
    
    if not match_data:
        return ""
        
    recommendation = match_data.get("RECOMENDACION", "")
    if not recommendation:
        return ""
        
    # Extraemos estadísticas en vivo para evaluar
    live_shots = 0
    live_red_cards = 0
    for s in stats:
        if s['category'] == 'Total shots':
            live_shots = int(s['home']) + int(s['away'])
        if s['category'] == 'Red cards':
            live_red_cards = int(s['home']) + int(s['away'])
            
    note = f"Predicción base: <b>{recommendation}</b>.\n"
    
    # Regla 1: Over 2.5 pero va 0-0 con muchos tiros
    # Parseamos score e.g "0:0"
    is_0_0 = score == "0:0" or score == "0-0"
    
    # OJO: match_time puede tener formato "2nd Half - 61'" o "1st Half - 30'"
    # intentamos buscar un número
    import re
    minutes = re.findall(r'\d+', match_time)
    current_minute = int(minutes[-1]) if minutes else 0
    
    if "2.5" in recommendation and "OVER" in recommendation.upper():
        if is_0_0 and current_minute >= 30 and live_shots >= 10:
            return note + "🔥 <b>OPORTUNIDAD:</b> Alta presión en el área, el gol está al caer."
        if current_minute >= 60 and is_0_0 and live_shots < 8:
            return note + "⚠️ <b>CUIDADO:</b> El partido no sigue el guion previsto. Falta de llegadas claras."
            
    # Regla 2: Hubo expulsión y cambia el panorama para el favorito
    if live_red_cards > 0:
        return note + "⚠️ <b>CUIDADO:</b> Tarjeta roja en el partido, precaución con el pronóstico inicial."
        
    return note
