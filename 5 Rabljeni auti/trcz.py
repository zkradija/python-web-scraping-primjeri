from datetime import date, datetime
import time
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
from openpyxl import load_workbook
import math

from selenium import webdriver 
from selenium.webdriver import Chrome 
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By 
from webdriver_manager.chrome import ChromeDriverManager



# vrijeme izvođenja --> 1 min
# nema datuma objave pa ću staviti trenutni datum

# NAPOMENA - na ovoj stranici se mora isključiti javascript. inače se ne parsiraju dobro podaci (uvijek pasrira 1 stranicu !!!)
# to rješavamo tako da isključimo javascriptu pomoću seleniuma pa tek onda vadimo podatke s BS


options = webdriver.ChromeOptions() 
options.add_argument('--headless')
options.add_experimental_option( "prefs",{'profile.managed_default_content_settings.javascript': 2})
options.page_load_strategy = 'none' 
# this returns the path web driver downloaded 
chrome_path = ChromeDriverManager().install() 
chrome_service = Service(chrome_path) 
# pass the defined options and service objects to initialize the web driver 
driver = Chrome(options=options, service=chrome_service) 

# identificiram se kao Firefox browser
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/111.0.1', 'Accept-Encoding': '*', 'Connection': 'keep-alive'}
s = requests.Session()


def parse(url):

    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglasi = []
    for div in soup.find_all('div', {'class': 'article-content'}):
        link = 'https://www.trcz.hr' + str(div.a['href']).strip().split('?')[0]
        oglasi.append(link)
    return oglasi


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','',''] 
    oglas_det[0] = 'TRCZ automobili'  # ime oglasnika
    oglas_det[1] = (str(url))   # poveznica
    oglas_det[2] =  'TRCZ automobili'  # prodavač
    if soup.find('p', {'class' : 'price Eu-price'}) is not None: 
        oglas_det[11] = float(soup.find('p', {'class' : 'price Eu-price'}).getText().split(' €')[0].strip().replace('.','').replace(',','.'))   # cijena
    oglas_det[12] = date.today().strftime('%d.%m.%Y')  # datum objave uvijek isti
    if soup.find('li', {'class' : 'main-item on'}).find('ul').find('li', {'class' : 'on'}) is not None: 
        oglas_det[3] = soup.find('li', {'class' : 'main-item on'}).find('ul').find('li', {'class' : 'on'}).getText().strip()  # marka
    if soup.find('ul', {'id' : 'articlesMenu'}).find('li', {'class' : 'on'}) is not None: 
        oglas_det[4] = soup.find('ul', {'id' : 'articlesMenu'}).find('li', {'class' : 'on'}).getText().split('(')[0].strip()     # model
        
    # da dobijem tip, izbijam i marku i model
    if soup.find('div', {'id' : 'article-header'}).find('h1') is not None: 
        ime_auta = soup.find('div', {'id' : 'article-header'}).find('h1').getText()
        marka_auta = oglas_det[3]
        model_auta = oglas_det[4]
        if marka_auta in ime_auta: ime_auta_bez_marke = ime_auta.replace(marka_auta,'')
        if model_auta in ime_auta_bez_marke: oglas_det[5] = ime_auta_bez_marke.replace(model_auta,'').strip()    # tip

    for tr in soup.find('div', {'id' : 'article-details'}).find_all('tr'):
        match tr.find('th').getText().strip():
            case 'Vrsta motora:':
                oglas_det[6] = str(tr.find('td').get_text().strip())
            case 'Kilometraža:':
                oglas_det[7] = int(tr.find('td').get_text().split(' ')[0].strip().replace('.',''))
            case 'Godina proizvodnje:':
                oglas_det[8] = int(tr.find('td').get_text().strip())
            case 'Snaga vozila:':
                oglas_det[9] = int(tr.find('td').get_text().split(' ')[0].strip())
            case 'Boja vozila:':
                oglas_det[10] = str(tr.find('td').get_text().strip())
    return oglas_det


def oglasi(w, t):
    workers=w
    time_sleep=t
    # provjera je li javascript isključen
    # driver.get('https://www.whatismybrowser.com/detect/is-javascript-enabled') 
    print ('TRCZ automobili')
    oglasi = []
    pocetak_vrijeme = time.time()
    last_page = 1
    response = s.get('https://www.trcz.hr/rabljena-vozila-3.aspx?page=1',headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")

    last_page = math.ceil(int(soup.find('div', {'id' : 'articles-no'}).get_text().split(',')[0].split(':')[1].strip())/12)
    print('Zadnja stranica pronađena: ' + str(last_page) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    
    URLs = []
    for i in range (1, last_page + 1):
        URLs.append('https://www.trcz.hr/rabljena-vozila-3.aspx?page=' + str(i))
    URLs2 = []

    # prvo parsiram url stranice na kojoj je popis sa po 100 oglasa
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [ executor.submit(parse, url) for url in URLs ]
        for result in as_completed(futures):
            for oglas in result.result():
                URLs2.append(oglas)
                time.sleep(time_sleep/5)                 
        print('Zaglavlja oglasa napunjena: ' + datetime.now().strftime("%H:%M:%S") + ' h')

    br_oglasa=1
    # sad parsiram stranicu pojedinačnog oglasa
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [ executor.submit(parse_oglas, url) for url in URLs2]
        for result in as_completed(futures):
            oglasi.append(result.result())
            time.sleep(time_sleep)            
            if br_oglasa == 1 or br_oglasa % 500 == 0: print('Oglas broj: ' + str(br_oglasa) + ' / ' + str(len(URLs2)) + ' --> ' + datetime.now().strftime("%H:%M") + ' h')
            br_oglasa += 1

    driver.quit()

    # preventivno čistim ako ima neispravnih / praznih oglasa, te starijih od 2013 godine
    for ele in oglasi:
        if ele is None or ele[8] < 2013: 
            oglasi.remove(ele)

    wb = load_workbook(filename = './5 Rabljeni auti/Rabljeni_auti.xlsx')
    sheet = wb.active

    for oglas in oglasi:
        sheet.append(oglas)

    wb.save (filename = './5 Rabljeni auti/Rabljeni_auti.xlsx')

   
    kraj_vrijeme = time.time()
    ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
    print('TRCZ automobili: ' + str(round(ukupno_vrijeme,0)) + ' sekundi')

if __name__ == '__main__':
    oglasi()