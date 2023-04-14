from datetime import date, datetime
import time
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
from openpyxl import load_workbook

# vrijeme izvođenja --> 1 min
# nema datuma objave pa ću staviti trenutni datum

# identificiram se kao Chrome browser
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36', 'Accept-Encoding': '*', 'Connection': 'keep-alive'}
s = requests.Session()


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','',''] 
    oglas_det[0] = 'Auto Hrvatska'  # ime oglasnika
    oglas_det[1] = (str(url))   # poveznica
    oglas_det[2] =  'Auto Hrvatska'  # prodavač
    if soup.find('span', {'class' : 'full-price Eu-price'}) is not None: 
        oglas_det[11] = float(soup.find('span', {'class' : 'full-price Eu-price'}).getText().split(' €')[0].strip().replace('.','').replace(',','.'))   # cijena
    oglas_det[12] = date.today().strftime('%d.%m.%Y')  # datum objave uvijek isti
        
    for li in soup.find('ul', {'class' : 'col-one'}).find_all('li'):
        match li.find('span', {'class', 'description'}).getText().strip():
            case 'Marka vozila:':
                oglas_det[3] = li.find('span', {'class' : 'value'}).getText().strip().title()
            case 'Model:':
                oglas_det[4] = li.find('span', {'class' : 'value'}).getText().strip().title()
            case 'Motor:':
                oglas_det[5] = li.find('span', {'class' : 'value'}).getText().strip()
            case 'Vrsta motora:':
                oglas_det[6] = li.find('span', {'class' : 'value'}).getText().strip().title()
            case 'Kilometraža:':
                oglas_det[7] = int(li.find('span', {'class' : 'value'}).getText().replace(' km','').strip().replace('.',''))
            case 'Godina proizvodnje:':
                oglas_det[8] = int(li.find('span', {'class' : 'value'}).getText().strip()[:4])
            case 'Snaga motora:':
                oglas_det[9] = int(li.find('span', {'class' : 'value'}).getText().strip().split(' ')[0].strip())
    for li in soup.find('ul', {'class' : 'col-two'}).find_all('li'):
        match li.find('span', {'class', 'description'}).getText().strip():
            case 'Boja:':
                oglas_det[10] = li.find('span', {'class' : 'value'}).getText().strip().title()
                break
    return oglas_det


def oglasi(w, t):
    workers=w
    time_sleep=t
    print ('Auto Hrvatska')
    oglasi = []
    pocetak_vrijeme = time.time()
    

    response = s.get('https://rabljena.autohrvatska.hr/rezultati-pretrage.aspx?uid=HjEbL0OA159&size=all',headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
   
    #ne treba izračun last_page jer ima opcija za prikaz svih oglasa
    print('Zadnja stranica pronađena: ' + str(1) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    
    URLs2 = []

    for h2 in soup.find('div', {'class' : 'row cf'}).find_all('h2', {'class' : 'car-title'}):
        URLs2.append('https://rabljena.autohrvatska.hr/' + h2.a['href'])
    
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
    print('Auto Hrvatska: ' + str(round(ukupno_vrijeme,0)) + ' sekundi')

if __name__ == '__main__':
    oglasi()