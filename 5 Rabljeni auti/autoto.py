from datetime import date, datetime
import time
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
from openpyxl import load_workbook

# vrijeme izvođenja --> 1 min
# nema datuma objave pa ću staviti trenutni datum

# treba mi popis marki i modela. radim global varijablu, da mogu koristiti u funkciji parse_oglas()
global marka
marka = []

global model
model = []

# identificiram se kao Firefox browser
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36', 'Accept-Encoding': '*', 'Connection': 'keep-alive'}
s = requests.Session()

response = s.get('https://www.autoto.hr/',headers=headers)
web_page = response.text
soup = BeautifulSoup(web_page, "html.parser")

# marka
for o in soup.find('select', {'id' : 'select-catalogFilterSection-Brand'}).find_all('option'):
    marka.append(o.getText().strip())

# model
for o in soup.find('select', {'id' : 'select-catalogFilterSection-BrandAndModel'}).find_all('option'):
    for m in marka:
        if m in o.getText().strip():
            model_tmp = []
            model_tmp.append(o.getText().replace(m,'').strip())
            model_tmp.append(o.getText().strip())
            model.append(model_tmp)
            break
        else:
            continue
        break
        


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','',''] 
    oglas_det[0] = 'Autoto'  # ime oglasnika
    oglas_det[1] = (str(url))   # poveznica
    oglas_det[2] =  'Autoto'  # prodavač
    
    if soup.find('header', {'class' : 'catalog-header'}).find('h1') is not None:
        for ma in marka:
            if ma in soup.find('header', {'class' : 'catalog-header'}).find('h1').get_text():
                oglas_det[3] = ma
                break
        
        for mo in model:
            if mo[1] in soup.find('header', {'class' : 'catalog-header'}).find('h1').get_text():    #ovdje sam uzeo mo[1] umjesto m[0] jer se u m[0] nalazi i prazan element ['', 'Sve'] pa uvijek njega uzme
                oglas_det[4] = mo[0]
                break
        
        #tip
        for tip in model:
            if tip[1] in soup.find('header', {'class' : 'catalog-header'}).find('h1').get_text():
                oglas_det[5] = soup.find('header', {'class' : 'catalog-header'}).find('h1').get_text().replace(tip[1],'').strip()
                break

    
    if soup.find('div', {'class' : 'article-price'}).find('strong', {'class' : 'price-compare-euro'}) is not None: 
        oglas_det[11] = float(soup.find('div', {'class' : 'article-price'}).find('strong', {'class' : 'price-compare-euro'}).getText().split(' €')[0].strip().replace('.','').replace(',','.'))   # cijena
    oglas_det[12] = date.today().strftime('%d.%m.%Y')  # datum objave uvijek isti
        
    for span in soup.find('div', {'class' : 'specs-box col c8 tablet-c8 mob-c24 specs-tech open'}).find_all('span', {'class' : 'label'}):
        match span.getText().strip():
            case 'Vrsta goriva:':
                oglas_det[6] =  span.find_next_sibling('span').getText().strip()
            case 'Kilometraža:':
                oglas_det[7] = int(span.find_next_sibling('span').getText().replace(' km','').strip().replace('.',''))
            case 'U prometu od:':
                oglas_det[8] = int(span.find_next_sibling('span').getText().strip()[-5:-1])
            case 'Snaga vozila:':
                oglas_det[9] = int(span.find_next_sibling('span').getText().split(' ')[0].strip())
            case 'Boja vozila:':
                oglas_det[10] = span.find_next_sibling('span').getText().strip()
    return oglas_det


def oglasi(w, t):
    workers=w
    time_sleep=t
    print ('Autoto')
    oglasi = []
    pocetak_vrijeme = time.time()
    
    response = s.get('https://www.autoto.hr/rezultati-pretrage.aspx?uid=VsfRjY27&size=all',headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
   
    #ne treba izračun last_page jer ima opcija za prikaz svih oglasa
    print('Zadnja stranica pronađena: ' + str(1) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    
    URLs2 = []

    for h2 in soup.find_all('p', {'class' : 'article-title'}):
        URLs2.append('https://www.autoto.hr' + h2.a['href'])
    
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
    print('Autoto: ' + str(round(ukupno_vrijeme,0)) + ' sekundi')

if __name__ == '__main__':
    oglasi()