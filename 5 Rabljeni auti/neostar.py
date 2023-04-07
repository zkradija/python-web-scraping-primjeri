from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import time
import xlsxwriter
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed


# vrijeme izvođenja --> 9 min
# nema datuma objave pa ću staviti trenutni datum


workers = 24    # obično se stavlja broj logičkih procesora. napomena: The number of workers must be less than or equal to 61 if Windows is your operating system.
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
    for div in soup.find_all('div', {'class': 'card-body p-0'}):
        link = 'https://www.neostar.com/' + str(div.a['href']).strip()
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
        oglas_det[12] = date.today()  # datum objave uvijek isti
    except:
        pass
    try:
        if soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText()[:9] == 'Alfa Romeo':
            oglas_det[3] = 'Alfa Romeo'
            model_txt_start = 10
            model_txt_end = int(soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().strip().find(',')) - 1 
            oglas_det[4] = soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText()[model_txt_start : model_txt_end]
        elif soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText()[:9] == 'Land Rover':
            oglas_det[3] = 'Land Rover'
            model_txt_start = 10
            model_txt_end = int(soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().strip().find(',')) - 1
            oglas_det[4] = soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText()[model_txt_start : model_txt_end]
        else:
            marka_txt_start = int(soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().strip().find(' '))
            marka_txt_end = int(len(soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().strip()))
            oglas_det[3] = soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText()[marka_txt_start : marka_txt_end]    # marka
            model_txt_start = int(soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().strip().find(' ')) + 1 
            model_txt_end = int(soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText().strip().find(',')) - 1 
            oglas_det[4] = soup.find('div', {'class' : 'vehicle-details-title pr-2'}).getText()[model_txt_start : model_txt_end]    # model

        # tip
        if soup.find('span', {'class' : 'text-center black-text vehicle-type'}) is not None: oglas_det[5] = soup.find('span', {'class' : 'text-center black-text vehicle-type'}).getText().strip()

        for div in soup.find_all('span', {'class' : 'row my-3 p-2 vehicle-info-item'}):
            match str(div.find('div', {'class' : 'col-6 d-inline-flex justify-content-start vehicle-info-title'})):
                case 'VRSTA GORIVA':
                    oglas_det[6] = str(div.find_next_sibling('div').get_text())
                case 'KM':
                    oglas_det[7] = str(div.find_next_sibling('div').get_text())
                case 'GODIŠTE':
                    oglas_det[8] = str(div.find_next_sibling('div').get_text())
                case 'SNAGA MOTORA (KW)':
                    oglas_det[9] = str(div.find_next_sibling('div').get_text())
                case 'BOJA':
                    oglas_det[10] = str(div.find_next_sibling('div').get_text())
        return oglas_det
    except:
        pass


def oglasi():
    oglasi = []
    pocetak_vrijeme = time.time()
    last_page = 1
    response = s.get('https://www.neostar.com/hr/buy-vehicle?year_from=2014&year_to=2022&sort=3&page=1',headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")

    last_page = int(soup.find('ul', {'class': 'pagination pg-blue justify-content-center align-content-center'}).find_all('li')[-3].text.strip())
    print('Zadnja stranica pronađena: ' + str(last_page) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    
    URLs= []
    for i in range (0, last_page + 1):
        URLs.append('https://www.neostar.com/hr/buy-vehicle?year_from=2014&year_to=2022&sort=3&page=' + str(i))
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


    #brišem starije od 6 mjeseci:
    for ele in oglasi:
        if len(ele[12].strip()) > 0 :
            if date.today() - relativedelta(months = 6) > datetime.strptime(ele[12], '%d.%m.%Y').date():
                oglasi.remove(ele)

    #upisujem podatke u Excel
    with xlsxwriter.Workbook('Rabljeni_auti_Index.xlsx') as workbook:
        worksheet = workbook.add_worksheet('Index')

        #dodajem zaglavlje
        worksheet.write(0, 0, 'oglasnik')
        worksheet.write(0, 1, 'poveznica')
        worksheet.write(0, 2, 'prodavac')
        worksheet.write(0, 3, 'marka')
        worksheet.write(0, 4, 'model')
        worksheet.write(0, 5, 'tip')
        worksheet.write(0, 6, 'motor')
        worksheet.write(0, 7, 'kilometraza')
        worksheet.write(0, 8, 'godina_proizvodnje')
        worksheet.write(0, 9, 'snaga_motora_kW')
        worksheet.write(0, 10, 'boja')
        worksheet.write(0, 11, 'cijena')
        worksheet.write(0, 12, 'datum_objave')

        for row_num, oglasi in enumerate(oglasi):
            worksheet.write_row(row_num+1, 0, oglasi)
    
    kraj_vrijeme = time.time()
    ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
    print(str(ukupno_vrijeme) + ' sekundi')


if __name__ == '__main__':
    print ('Neostar')
    oglasi()