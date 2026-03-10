from bs4 import BeautifulSoup
html = open('flashscore_page.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')
# Buscamos divs que tengan poco texto para ver si encontramos el marcador "2:1" o el tiempo "45'"
for div in soup.find_all('div'):
    t = div.text.strip()
    if len(t) < 10 and (':' in t or "'" in t or 'Halftime' in t or 'Finished' in t):
        print(div.get('class'), t)
