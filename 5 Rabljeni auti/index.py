from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import time
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
import openpyxl
import math


# vrijeme izvođenja --> 7 min
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
    for div in soup.find_all('div', {'class': 'OglasiRezHolder'}):
        if div.find('a', {'class': 'result'}) is not None :
            link = str(div.a['href']).strip()
            oglasi.append(link)
    return oglasi


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    time.sleep(time_sleep)
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','','']   
    oglas_det[0] = 'Index'  # ime oglasnika
    oglas_det[1] = (str(url))   #poveznica
    if soup.find('a', {'class' : 'oglasKorisnickoIme'}) is not None : oglas_det[2] = soup.find('a', {'class' : 'oglasKorisnickoIme'}).get_text() # prodavač
    try: 
        if soup.find('div', {'class' : 'price'}) is not None: oglas_det[11] = int(str(soup.find('div', {'class' : 'price'}).find('span').get_text()).replace(' €', '').replace('.',''  ).replace(',',''))   #cijena 
        datum_objave_str_start = int(str(soup.find('div', {'class' : 'published'})).find('Objava: ')) + 8
        datum_objave_str_end = int(str(soup.find('div', {'class' : 'published'})).find('Objava: ')) + 18
        if soup.find('div', {'class' : 'published'}) is not None: oglas_det[12] = str(soup.find('div', {'class' : 'published'}))[datum_objave_str_start : datum_objave_str_end]  #datum objave, 
          
    except:
        pass
    try:
        #tražim osnovne podatke o vozilu unutar features_list oglasHolder_1
        for div in soup.find_all('div', {'class' : 'features_list oglasHolder_1'}):
            for li in div.find_all('li'):
                match str(li.get_text()):
                    case 'Marka:':
                        oglas_det[3] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                    case 'Model:':
                        oglas_det[4] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                    case 'Tip:':
                        oglas_det[5] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                    case 'Motor':
                        oglas_det[6] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                    case 'Prijeđeni kilometri':
                        oglas_det[7] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','').replace('.',''  ).replace(',','')
                    case 'Godina proizvodnje':
                        oglas_det[8] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                    case 'Snaga motora kW':
                        oglas_det[9] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                    case 'Boja vozila':
                        oglas_det[10] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
        return oglas_det
    except:
        pass    

def oglasi():
    print ('Index')
    oglasi = []
    pocetak_vrijeme = time.time()
    last_page = 1
    response = s.get('https://www.index.hr/oglasi/osobni-automobili/gid/27?pojam=&sortby=3&elementsNum=100&cijenaod=3500&attr_Int_179=2013&attr_Int_1190=2022&attr_Int_470=1&attr_Int_910=&attr_bit_349=1&attr_bit_350=1&attr_bit_351=1&vezani_na=179-1190_470-910_1172-1335_359-1192&num=1',headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")

    for li in soup.find("ul", {'class': 'pagination'}).find_all("li"):
        li_split = (str(li).split("num="))
        if len(li_split) == 2:
            li_split2 = li_split[1].split("\">")
            if int(li_split2[0]) > last_page:
                last_page =  int(li_split2[0])
    print('Zadnja stranica pronađena: ' + str(last_page) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    
    URLs= []
    for i in range (0, last_page + 1):
        URLs.append('https://www.index.hr/oglasi/osobni-automobili/gid/27?pojam=&sortby=3&elementsNum=100&cijenaod=3500&attr_Int_179=2013&attr_Int_1190=2022&attr_Int_470=1&attr_Int_910=&attr_bit_349=1&attr_bit_350=1&attr_bit_351=1&vezani_na=179-1190_470-910_1172-1335_359-1192&num=' + str(i))
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


    oglasi.insert(0, ['oglasnik','poveznica','prodavac','marka','model','tip','motor','kilometraza','godina_proizvodnje','snaga_motora','boja','cijena','datum_objave'])

    wb = openpyxl.Workbook()
    sheet = wb.active

    for oglas in oglasi:
        sheet.append(oglas)

    wb.save (filename = './5 Rabljeni auti/Rabljeni_auti.xlsx')

   
    kraj_vrijeme = time.time()
    ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
    print('Index: ' + str(round(ukupno_vrijeme,0)) + ' sekundi')

if __name__ == '__main__':
    oglasi()