from datetime import date, datetime
import time
import xlsxwriter
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
from openpyxl import load_workbook
import math

# vrijeme izvođenja --> 6 min
# nema datuma objave pa ću staviti trenutni datum


workers = 30    # obično se stavlja broj logičkih procesora. napomena: The number of workers must be less than or equal to 61 if Windows is your operating system.
time_sleep = 1


# treba mi popis marki. radim global varijablu, da mogu koristiti u funkciji parse_oglas()
global marka
marka = []

# identificiram se kao Firefox browser
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/111.0.1', 'Accept-Encoding': '*', 'Connection': 'keep-alive'}
s = requests.Session()

response = s.get('https://www.neostar.com/hr/buy-vehicle?year_from=2013&year_to=2022&sort=3&page=1',headers=headers)
web_page = response.text
soup = BeautifulSoup(web_page, "html.parser")

for o in soup.find('select', {'id' : 'makeSelect'}).find_all('option'):
    marka.append(o.getText().strip())

def parse(url):
    time.sleep(time_sleep)
    response = s.get(url, headers=headers)
    web_page = response.text
    soup = BeautifulSoup(web_page, "html.parser")
    oglasi = []
    for div in soup.find_all('div', {'class': 'card-body p-0'}):
        link = 'https://www.neostar.com' + str(div.a['href']).strip()
        oglasi.append(link)
    return oglasi


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    time.sleep(time_sleep)
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','',''] 
    oglas_det[0] = 'Neostar'  # ime oglasnika
    oglas_det[1] = (str(url))   # poveznica
    oglas_det[2] = 'Neostar' # prodavač
    try: 
        if soup.find('span', {'class' : 'price secondaryPrice'}) is not None: oglas_det[11] = float(str(soup.find('span', {'class' : 'price secondaryPrice'}).get_text()).strip().replace(' €','').replace('.','').replace(',','.'))   #cijena 
        oglas_det[12] = date.today().strftime('%d.%m.%Y')  # datum objave uvijek isti
    except:
        pass
    if soup.find('div', {'class' : 'vehicle-details-title pr-2'}) is not None:  # ovo stavljam za slučaj da neki oglas nestane u tijeku scrapanja
        # nema zasebnog polja za marku i model pa ih moram izvlačiti. koristit ću marku iz padajućeg izbornika
        for m in marka:
            if m.lower() in soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().strip().lower():   
                oglas_det[3] = m    # marka
                break

        if oglas_det[3].lower() in soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().strip().lower():    # model
            oglas_det[4] = soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().replace(oglas_det[3],'').split(',')[0].strip()
        # tip
        if soup.find('span', {'class' : 'text-center black-text vehicle-type'}) is not None: oglas_det[5] = soup.find('span', {'class' : 'text-center black-text vehicle-type'}).getText().strip()

        for div in soup.find_all('div', {'class' : 'row my-3 p-2 vehicle-info-item'}):
            if div.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title'}) is not None:
                match div.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title'}).getText().strip():
                    case 'Vrsta goriva':
                        oglas_det[6] = str(div.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title'}).find_next_sibling('div').get_text().strip())
                    case 'Km':
                        oglas_det[7] = str(div.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title'}).find_next_sibling('div').get_text().replace(' km','').replace('.','').strip())
                    case 'Godište':
                        oglas_det[8] = str(div.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title'}).find_next_sibling('div').get_text().strip())
                    case 'Snaga motora (kW)':
                        oglas_det[9] = str(div.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title'}).find_next_sibling('div').get_text().strip().split(' ')[0])
        
        if soup.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title align-content-center'}) is not None:
            oglas_det[10] = soup.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title align-content-center'}).find_next_sibling('div').get_text().strip()
        return oglas_det


def oglasi():
    print ('Neostar')
    oglasi = []
    pocetak_vrijeme = time.time()
    last_page = 1
    response = s.get('https://www.neostar.com/hr/buy-vehicle?year_from=2013&year_to=2022&sort=3&page=1',headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")

    last_page = int(soup.find('ul', {'class': 'pagination pg-blue justify-content-center align-content-center'}).find_all('li')[-3].text.strip())
    print('Zadnja stranica pronađena: ' + str(last_page) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    
    URLs= []
    for i in range (1, last_page + 1):
        URLs.append('https://www.neostar.com/hr/buy-vehicle?year_from=2013&year_to=2022&sort=3&page=' + str(i))
    URLs2 = []

    # prvo parsiram url stranice na kojoj je popis sa po 100 oglasa
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [ executor.submit(parse, url) for url in URLs ]
        for result in as_completed(futures):
            for oglas in result.result():
                URLs2.append(oglas)
        print('Zaglavlja oglasa napunjena: ' + datetime.now().strftime("%H:%M:%S") + ' h')

    br_oglasa=1
    # sad parsiram stranicu pojedinačnog oglasa
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [ executor.submit(parse_oglas, url) for url in URLs2]
        for result in as_completed(futures):
            oglasi.append(result.result())
            if br_oglasa == 1 or br_oglasa % 500 == 0: print('Oglas broj: ' + str(br_oglasa) + ' / ' + str(len(URLs2)) + ' --> ' + datetime.now().strftime("%H:%M") + ' h')
            br_oglasa += 1

    # čistim od neispravnih / praznih oglasa
    for ele in oglasi:
        if ele is None: 
            oglasi.remove(ele)

    wb = load_workbook(filename = './5 Rabljeni auti/Rabljeni_auti.xlsx')
    sheet = wb.active

    for oglas in oglasi:
        sheet.append(oglas)

    wb.save (filename = './5 Rabljeni auti/Rabljeni_auti.xlsx')

   
    kraj_vrijeme = time.time()
    ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
    print('Neostar: ' + str(round(ukupno_vrijeme,0)) + ' sekundi')


if __name__ == '__main__':
    oglasi()