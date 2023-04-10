import index, neostar, dasweltauto, trcz, autohrvatska, autoto


from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import time
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
import openpyxl
import math


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/111.0.1', 'Accept-Encoding': '*', 'Connection': 'keep-alive'}
    s = requests.Session()

    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','','']   
    oglas_det[0] = 'Index'  # ime oglasnika
    oglas_det[1] = (str(url))   #poveznica
    if soup.find('a', {'class' : 'oglasKorisnickoIme'}) is not None : oglas_det[2] = soup.find('a', {'class' : 'oglasKorisnickoIme'}).get_text().strip() # prodavač
    if oglas_det[2] == 'Auto Mall':
        print(oglas_det)
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




if __name__ == '__main__':
    #index.oglasi()
    #neostar.oglasi()
    #dasweltauto.oglasi()
    #trcz.oglasi()
    #autohrvatska.oglasi()
    #autoto.oglasi()
    parse_oglas('https://www.index.hr/oglasi/opel-combo-1-5-cdti-n1/oid/3967780')