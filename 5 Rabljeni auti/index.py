from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import time
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
import openpyxl


# vrijeme izvođenja -->  24 min sa workers = 30


# identificiram se kao Firefox browser
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36', 'Accept-Encoding': '*', 'Connection': 'keep-alive'}
s = requests.Session()



def parse(url):
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
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','','']   
    oglas_det[0] = 'Index'  # ime oglasnika
    oglas_det[1] = (str(url))   #poveznica
    if soup.find('a', {'class' : 'oglasKorisnickoIme'}) is not None : oglas_det[2] = soup.find('a', {'class' : 'oglasKorisnickoIme'}).get_text().strip() # prodavač
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
                        oglas_det[7] = int(str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','').replace('.',''  ).replace(',',''))
                    case 'Godina proizvodnje':
                        oglas_det[8] = int(str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n',''))
                    case 'Snaga motora kW':
                        oglas_det[9] = int(str(li.find_next_sibling('li').get_text()).replace('.','').replace(',','').replace('\r','').replace('\n',''))
                    case 'Boja vozila':
                        oglas_det[10] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
        
        # provjeravam jesu li marka i model prazni - postoji bug na indexovoj stranici - nakon refreshanja stranice misteriozno nestanu marka i model
        # taj bug ću zaobići čitanjem marke i modela iz breadcrumba
        try:
            if soup.find('ul', {'id':'bread'}).find_all('li') is not None:  # ovo ubacujem za slučaj da je oglas u međuvremenu obrisan
                if len(soup.find('ul', {'id':'bread'}).find_all('li')) > 4 :
                    if oglas_det[3] == '': oglas_det[3] = soup.find('ul', {'id':'bread'}).find_all('li')[3].get_text().strip()
                    if oglas_det[4] == '': oglas_det[4] = soup.find('ul', {'id':'bread'}).find_all('li')[4].get_text().strip()
        except:
            pass
        return oglas_det
    except:
        pass    

def oglasi(w, t):
    workers=w
    time_sleep=t
    print ('Index')
    oglasi = []
    pocetak_vrijeme = time.time()
    last_page = 1
    response = s.get('https://www.index.hr/oglasi/osobni-automobili/gid/27?pojamZup=-2&tipoglasa=1&sortby=1&elementsNum=100&grad=0&naselje=0&cijenaod=3500&cijenado=49000000&attr_Int_179=2013&attr_Int_1190=2022&attr_Int_470=1&vezani_na=179-1190_470-910_1172-1335_359-1192&num=1',headers=headers)
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
    for i in range (1, last_page + 1):
        URLs.append('https://www.index.hr/oglasi/osobni-automobili/gid/27?pojamZup=-2&tipoglasa=1&sortby=1&elementsNum=100&grad=0&naselje=0&cijenaod=3500&cijenado=49000000&attr_Int_179=2013&attr_Int_1190=2022&attr_Int_470=1&vezani_na=179-1190_470-910_1172-1335_359-1192&num=' + str(i))
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

    # čistim od neispravnih / praznih oglasa
    for ele in oglasi:
        if ele is None: 
            oglasi.remove(ele)



    # mičem starije oglase
    for ele in oglasi:
        if len(ele[12].strip()) > 0 :
            if date.today() - relativedelta(months = 6) > datetime.strptime(ele[12], '%d.%m.%Y').date():
                oglasi.remove(ele)


    oglasi.insert(0, ['oglasnik','poveznica','prodavac','marka','model','tip','motor','kilometraza','godina_proizvodnje','snaga_motora','boja','cijena','datum_objave'])

    wb = openpyxl.Workbook()
    sheet = wb.active

    for oglas in oglasi:
        sheet.append(oglas)

    wb.save (filename = './Rabljeni_auti.xlsx')

   
    kraj_vrijeme = time.time()
    ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
    print('Index: ' + str(round(ukupno_vrijeme,0)) + ' sekundi')

if __name__ == '__main__':
    oglasi()