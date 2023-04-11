from datetime import date, datetime
import time
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
from openpyxl import load_workbook
import math
import re

# vrijeme izvođenja --> 2-3 min
# nema datuma objave pa ću staviti trenutni datum


# treba mi popis marki. radim global varijablu, da mogu koristiti u funkciji parse_oglas()
global marka
marka = []

# identificiram se kao Firefox browser
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36', 'Accept-Encoding': '*', 'Connection': 'keep-alive'}
s = requests.Session()

response = s.get('https://www.dasweltauto.hr/s?fromInitialRegistrationYear=2013&toInitialRegistrationYear=2022&pageSize=36&page=1',headers=headers)
web_page = response.text
soup = BeautifulSoup(web_page, "html.parser")

for o in soup.find('select', {'id' : 'brand-select'}).find_all('option'):
    marka.append(o.getText().split('(')[0].strip())



def parse(url):
    response = s.get(url, headers=headers)
    web_page = response.text
    soup = BeautifulSoup(web_page, "html.parser")
    oglasi = []
    for div in soup.find_all('div', {'class': 'name'}):
        link = 'https://www.dasweltauto.hr' + str(div.a['href']).strip().split('?')[0]
        oglasi.append(link)
    return oglasi


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','',''] 
    oglas_det[0] = 'DasWeltAuto'  # ime oglasnika
    oglas_det[1] = (str(url))   # poveznica
    if soup.find('div', {'class' : 'dealer-name'}) is not None:  oglas_det[2] =  soup.find('div', {'class' : 'dealer-name'}).get_text().strip() # prodavač
    if soup.find('div', {'class' : 'vehicle-price-effective'}) is not None: 
        oglas_det[11] = int(re.sub('[^0-9\.]','', soup.find('div', {'class' : 'vehicle-price-effective'}).getText()).replace('.',''))
    oglas_det[12] = date.today().strftime('%d.%m.%Y')  # datum objave uvijek isti
    
    # nema zasebnog polja za marku i model pa ih moram izvlačiti. koristit ću marku iz padajućeg izbornika
    if soup.find('div', {'class' : 'header'}) is not None: 
        for m in marka:
            if m.lower() in soup.find('div', {'class' : 'header'}).getText().strip().lower(): 
                oglas_det[3] = m    # marka
                break
    
    # sad izbijam model iz istog polja
    if oglas_det[3].lower() in soup.find('div', {'class' : 'header'}).getText().strip().lower(): 
        oglas_det[4] = soup.find('div', {'class' : 'header'}).getText().replace(oglas_det[3],'').strip()    # model
    
    if soup.find('div', {'class' : 'sub-header'}) is not None: oglas_det[5] = soup.find('div', {'class' : 'sub-header'}).getText().strip() # tip

    for li in soup.find('ul', {'class' : 'left-column'}).find_all('li'):
        match li.find('label').getText().strip():
            case 'Vrsta goriva':
                oglas_det[6] = str(li.find('span').get_text().strip())
            case 'Stanje km':
                if li.find('span').get_text().split(' ')[0].strip().replace('.','').isdigit(): oglas_det[7] = int(li.find('span').get_text().split(' ')[0].strip().replace('.',''))
            case 'Prva reg.':
                if str(li.find('span').get_text().strip())[-4:].isdigit(): oglas_det[8] = int(str(li.find('span').get_text().strip())[-4:])
            case 'Snaga':
                if li.find('span').get_text().split(' ')[0].strip().isdigit(): oglas_det[9] = int(li.find('span').get_text().split(' ')[0].strip())
            case 'Boja':
                    oglas_det[10] = str(li.find('span').get_text().strip())
    return oglas_det


def oglasi(w, t):
    workers=w
    time_sleep=t
    print ('DasWeltAuto')
    oglasi = []
    pocetak_vrijeme = time.time()
    last_page = 1
    response = s.get('https://www.dasweltauto.hr/s?fromInitialRegistrationYear=2013&toInitialRegistrationYear=2022&pageSize=36&page=1',headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")

    last_page = math.ceil(int(soup.find('span', {'id' : 'result-count'}).get_text().replace('.',''))/36)
    print('Zadnja stranica pronađena: ' + str(last_page) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    
    URLs = []
    for i in range (1, last_page + 1):
        URLs.append('https://www.dasweltauto.hr/s?fromInitialRegistrationYear=2013&toInitialRegistrationYear=2022&pageSize=36&page=' + str(i))
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

    # preventivno čistim ako ima neispravnih / praznih oglasa
    for ele in oglasi:
        if ele is None: 
            oglasi.remove(ele)

    wb = load_workbook(filename = './Rabljeni_auti.xlsx')
    sheet = wb.active

    for oglas in oglasi:
        sheet.append(oglas)

    wb.save (filename = './Rabljeni_auti.xlsx')

   
    kraj_vrijeme = time.time()
    ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
    print('DasWeltAuto: ' + str(round(ukupno_vrijeme,0)) + ' sekundi')

if __name__ == '__main__':
    oglasi()