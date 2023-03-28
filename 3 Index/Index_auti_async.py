from datetime import datetime
import time
import xlsxwriter
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed

# zadatak: sa internet stranice https://Index.hr skinuti sve oglase za automobile (cca 28.000 oglasa)
# filtrirat ćemo oglase - zanimaju nas samo oni oglasi koji imaju popunjena sva željena polja
# cca 5x brže radi nego verzija bez ProcessPoolExecutor. može i brže, ali onda se aktivira DDoS zaštita na serveru. zato usporavam sa time.sleep(1)


workers = 12    # obično se stavlja broj logičkih procesora. napomena: The number of workers must be less than or equal to 61 if Windows is your operating system.
data_gla = {}   # zaglavlje oglasa - treba mi šifra i županija, koju kasnije spajam s pojedinačnim oglasom, koristim dictionary radi lakšeg pozivanja županije preko šifre
data_det = []   # pojedičnačni oglasi; ne sadržavaju županiju
last_page = 1

# identificiram se kao Firefox browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/111.0.1",
    "Accept-Encoding": "*",
    "Connection": "keep-alive"}

pocetak_vrijeme = time.time()
s = requests.Session()

response = s.get('https://www.index.hr/oglasi/auto-moto/gid/27?&elementsNum=100&sortby=1&num=1',headers=headers)
web_page = response.content
soup = BeautifulSoup(web_page, "html.parser")

for li in soup.find("ul", {'class': 'pagination'}).find_all("li"):
    li_split = (str(li).split("num="))
    if len(li_split) == 2:
        li_split2 = li_split[1].split("\">")
        if int(li_split2[0]) > last_page:
            last_page =  int(li_split2[0])

#print(last_page)


URLs= []
for i in range (0, last_page+1):
    URLs.append('https://www.index.hr/oglasi/auto-moto/gid/27?&elementsNum=100&sortby=1&num=' + str(i))

def parse(url):
    time.sleep(1)
    response = s.get(url, headers=headers)
    web_page = response.text
    soup = BeautifulSoup(web_page, "html.parser")
    oglasi = []
    for div in soup.find_all('div', {'class': 'OglasiRezHolder'}):
        oglas = []
        if div.find('a', {'class': 'result'}) is not None :
            poveznica = str(div.a['href']).strip()
            sifra_oglasa_br = poveznica.find('/oid/') + 5
            sifra_oglasa = poveznica[-(len(poveznica)-sifra_oglasa_br):]
            if div.find('li', {'class': 'icon-marker'}) is not None :
                zupanija = div.find('li', {'class': 'icon-marker'}).get_text()
            else:
                zupanija=''
            oglas.append(sifra_oglasa)
            oglas.append(zupanija)
            oglas.append(poveznica)
            oglasi.append(oglas)
    return oglasi


def parse_oglas(url):
    #kreće otvaranje oglasa 1 po 1
    time.sleep(1)
    response = s.get(url, headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, "html.parser")
    oglas_det = ['','','','','','','','','','','','','','','','','','','','','','','','','','','','','','','','','']   
    oglas_det[0] = (str(url))
    if soup.find('a', {'class' : 'oglasKorisnickoIme'}) is not None : oglas_det[1] = soup.find('a', {'class' : 'oglasKorisnickoIme'}).get_text()
    if soup.find('div', {'class' : 'oglasivac_info grey_except_on_large'}) is not None:
        if len(soup.find('div', {'class' : 'oglasivac_info grey_except_on_large'}).find('ul').find_all('li')) >= 3 : 
            oglas_det[2] = str(soup.find('div', {'class' : 'oglasivac_info grey_except_on_large'}).find('ul').find_all('li')[3].get_text()).split(',')[0].strip()   #mjesto
    if soup.find("title") is not None : oglas_det[4] = (str(soup.find("title").get_text()).split(" | ")[0].strip())    #naslov
    if soup.find('div', {'class' : 'oglas_description'}) is not None: oglas_det[5] = str(soup.find('div', {'class' : 'oglas_description'}).get_text()).strip().replace('\r','') #opis
    if soup.find('div', {'class' : 'price'}) is not None: oglas_det[6] = int(str(soup.find('div', {'class' : 'price'}).find('span').get_text()).replace(' €', '').replace('.',''  ).replace(',',''))   #cijena
    if soup.find('div', {'class' : 'published'}) is not None: 
        oglas_det[7] = str(soup.find('div', {'class' : 'published'}).find('strong').get_text())    #šifra oglasa
        # if str(oglas_det[7]) != '' : 
        #     if str(oglas_det[7]) != '':
        #         oglas_det[3] = data_gla[oglas_det[7]]  
        #     else:
        #         oglas_det[3] = '' #zupanija
    datum_objave_str_start = int(str(soup.find('div', {'class' : 'published'})).find('Objava: ')) + 8
    datum_objave_str_end = int(str(soup.find('div', {'class' : 'published'})).find('Objava: ')) + 24
    if soup.find('div', {'class' : 'published'}) is not None: oglas_det[8] = str(soup.find('div', {'class' : 'published'}))[datum_objave_str_start : datum_objave_str_end]  #datum objave
    broj_prikaza_str_start = int(str(soup.find('div', {'class' : 'published'})).find('Prikazan: ')) + 10
    broj_prikaza_str_end = int(str(soup.find('div', {'class' : 'published'})).find(' puta')) 
    if soup.find('div', {'class' : 'published'}) is not None: oglas_det[9] = int(str(soup.find('div', {'class' : 'published'}))[broj_prikaza_str_start : broj_prikaza_str_end].strip())  #broj prikaza
    
    #tražim osnovne podatke o vozilu unutar features_list oglasHolder_1
    for div in soup.find_all('div', {'class' : 'features_list oglasHolder_1'}):
        for li in div.find_all('li'):
            match str(li.get_text()):
                case 'Marka:':
                    oglas_det[10] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Model':
                    oglas_det[11] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Tip:':
                    oglas_det[12] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Motor':
                    oglas_det[13] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Stanje vozila':
                    oglas_det[14] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Prijeđeni kilometri':
                    oglas_det[15] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','').replace('.',''  ).replace(',','')
                case 'Godina proizvodnje':
                    oglas_det[16] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Snaga motora kW':
                    oglas_det[17] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Godina modela':
                    oglas_det[18] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Prodavač':
                    oglas_det[19] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Registriran do':
                    oglas_det[20] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Boja vozila':
                    oglas_det[21] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Broj stupnjeva na mjenjaču':
                    oglas_det[22] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Broj vrata':
                    oglas_det[23] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Oblik karoserije':
                    oglas_det[24] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Prosječna potrošnja goriva l/100km':
                    oglas_det[25] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Radni obujam cm3':
                    oglas_det[26] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Ovjes':
                    oglas_det[27] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Starost':
                    oglas_det[28] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Vrsta pogona':
                    oglas_det[29] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Vrsta mjenjača':
                    oglas_det[30] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')

    for div in soup.find_all('div', {'class' : 'features_list oglasHolder_2'}):
        for li in div.find_all('li'):
            match str(li.get_text()):
                case 'Autoradio':
                    oglas_det[31] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
                case 'Klimatizacija vozila':
                    oglas_det[32] = str(li.find_next_sibling('li').get_text()).replace('\r','').replace('\n','')
    return oglas_det
        


if __name__ == '__main__':
    URLs2 = []
    print('Zadnja stranica pronađena: ' + str(last_page) + ' --> ' + datetime.now().strftime("%H:%M:%S") + ' h')
    # prvo parsiram url stranice na kojoj je popis sa po 100 oglasa
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [ executor.submit(parse, url) for url in URLs ]
        for result in as_completed(futures):
            for sifra in result.result():
                URLs2.append(sifra[2])
                data_gla[sifra[0]] = sifra[1]
        print('Zaglavlja oglasa napunjena: ' + datetime.now().strftime("%H:%M:%S") + ' h')

    br_oglasa=1
    # sad parsiram stranicu pojedinačnog oglasa
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [ executor.submit(parse_oglas, url) for url in URLs2]
        for result in as_completed(futures):
            for r in result.result():
                data_det.append(r)
            if br_oglasa == 1 or br_oglasa % 500 == 0: print('Oglas broj: ' + str(br_oglasa) + ' / ' + str(len(URLs2)) + ' --> ' + datetime.now().strftime("%H:%M") + ' h')
            br_oglasa += 1

    #upisujem podatke u Excel
    with xlsxwriter.Workbook('Index_auti_async.xlsx') as workbook:
        
        #kreiram list za pojedinačne oglase
        worksheet = workbook.add_worksheet('oglas_det')

        #dodajem zaglavlje
        worksheet.write(0, 0, 'poveznica')
        worksheet.write(0, 1, 'korisnicko_ime')
        worksheet.write(0, 2, 'mjesto')
        worksheet.write(0, 3, 'zupanija')
        worksheet.write(0, 4, 'naslov')
        worksheet.write(0, 5, 'opis')
        worksheet.write(0, 6, 'cijena')
        worksheet.write(0, 7, 'sifra_oglasa')
        worksheet.write(0, 8, 'datum_objave')
        worksheet.write(0, 9, 'broj_prikaza')
        worksheet.write(0, 10, 'marka')
        worksheet.write(0, 11, 'model')
        worksheet.write(0, 12, 'tip')
        worksheet.write(0, 13, 'motor')
        worksheet.write(0, 14, 'stanje_vozila')
        worksheet.write(0, 15, 'kilometraza')
        worksheet.write(0, 16, 'godina_proizvodnje')
        worksheet.write(0, 17, 'snaga_motora_kw')
        worksheet.write(0, 18, 'godina_modela')
        worksheet.write(0, 19, 'prodavac')
        worksheet.write(0, 20, 'registriran_do')
        worksheet.write(0, 21, 'boja_vozila')
        worksheet.write(0, 22, 'broj_stupnjeva_na_mjenjacu')
        worksheet.write(0, 23, 'broj_vrata')
        worksheet.write(0, 24, 'oblik_karoserije')
        worksheet.write(0, 25, 'potrosnja_goriva')
        worksheet.write(0, 26, 'radni_obujam_cm3')
        worksheet.write(0, 27, 'ovjes')
        worksheet.write(0, 28, 'starost')
        worksheet.write(0, 29, 'vrsta_pogona')
        worksheet.write(0, 30, 'vrsta_mjenjaca')
        worksheet.write(0, 31, 'autoradio')
        worksheet.write(0, 32, 'klimatizacija_vozila')

        for row_num, data_det in enumerate(data_det):
            worksheet.write_row(row_num+1, 0, data_det)
    
    kraj_vrijeme = time.time()
    ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
    print(ukupno_vrijeme)