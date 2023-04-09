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

workers = 30    # obično se stavlja broj logičkih procesora. napomena: The number of workers must be less than or equal to 61 if Windows is your operating system.
time_sleep = 1


# identificiram se kao Firefox browser
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/111.0.1', 'Accept-Encoding': '*', 'Connection': 'keep-alive'}
s = requests.Session()

def parse(url):
    time.sleep(time_sleep)
    response = s.get(url, headers=headers)
    web_page = response.text
    soup = BeautifulSoup(web_page, "html.parser")
    oglasi = []
    for div in soup.find_all('div', {'class': 'article-content'}):
        link = 'https://www.trcz.hr' + str(div.a['href']).strip().split('?')[0]
        oglasi.append(link)
    return oglasi


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    time.sleep(time_sleep)
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','',''] 
    oglas_det[0] = 'TRCZ automobili'  # ime oglasnika
    oglas_det[1] = (str(url))   # poveznica
    oglas_det[2] =  'TRCZ automobili' # prodavač
    if soup.find('p', {'class' : 'price Eu-price'}) is not None: 
        oglas_det[11] = float(soup.find('p', {'class' : 'price Eu-price'}).getText().strip().split(' ')[0].replace('.','').replace(',','.'))   # cijena
    oglas_det[12] = date.today().strftime('%d.%m.%Y')  # datum objave uvijek isti
    if soup.find('div', {'class' : 'header'}) is not None: oglas_det[3] = soup.find('div', {'class' : 'header'}).getText().strip().split(' ')[0]    # marka
    if len(soup.find('div', {'class' : 'header'}).getText().strip().split(' ')) > 1 : oglas_det[4] = soup.find('div', {'class' : 'header'}).getText().strip().split(' ')[1]    # model
    
    if soup.find('div', {'class' : 'sub-header'}) is not None: oglas_det[5] = soup.find('div', {'class' : 'sub-header'}).getText().strip() # tip

    for li in soup.find('ul', {'class' : 'left-column'}).find_all('li'):
        match li.find('label').getText().strip():
            case 'Vrsta goriva':
                oglas_det[6] = str(li.find('span').get_text().strip())
            case 'Stanje km':
                oglas_det[7] = li.find('span').get_text().split(' ')[0].strip().replace('.','')
            case 'Prva reg.':
                oglas_det[8] = str(li.find('span').get_text().strip())[-4:]
            case 'Snaga':
                oglas_det[9] = li.find('span').get_text().split(' ')[0].strip()
            case 'Boja':
                    oglas_det[10] = str(li.find('span').get_text().strip())
    return oglas_det


def oglasi():
    print ('TRCZ automobili')
    oglasi = []
    pocetak_vrijeme = time.time()
    last_page = 1
    response = s.get('https://www.trcz.hr/rezultati-pretrage.aspx?searchparam=p5~2013_2022#',headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")

    last_page = math.ceil(int(soup.find('div', {'id' : 'articles-no'}).get_text().split(',')[0].split(':')[1].strip())/36)
    print('Zadnja stranica pronađena: ' + str(last_page) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    
    URLs= []
    for i in range (1, last_page + 1):
        URLs.append('https://www.trcz.hr/rezultati-pretrage.aspx?searchparam=p5~2013_2022#'+ str(i) +' -10-6')
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

    # preventivno čistim ako ima neispravnih / praznih oglasa
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
    print('DasWeltAuto: ' + str(round(ukupno_vrijeme,0)) + ' sekundi')

if __name__ == '__main__':
    oglasi()