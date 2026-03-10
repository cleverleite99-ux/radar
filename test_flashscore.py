import sys
from playwright.sync_api import sync_playwright

# URL de prueba de Flashscore
URL = "https://www.flashscore.mobi/match/Cp7zG6DG/?t=stats"

def main():
    print("Iniciando Playwright...")
    with sync_playwright() as p:
        # Se establece headless=False para que puedas ver el navegador abriéndose. 
        # Cambiar a True si quieres que corra en segundo plano.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print(f"Navegando a: {URL}")
        page.goto(URL)
        
        # Esperar a que la página cargue completamente
        page.wait_for_load_state('networkidle')
        
        title = page.title()
        print(f"Título de la página: {title}")
        
        # Tomar una captura de pantalla como prueba
        screenshot_path = "flashscore_test.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Captura de pantalla guardada en: {screenshot_path}")
        
        print("Cerrando el navegador...")
        browser.close()

if __name__ == "__main__":
    main()
