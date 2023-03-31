from datetime import datetime
import time
import xlsxwriter
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By

# zadatak: sa internet stranice https://popusti.njuskalo.hr skinuti sve artikle koji su trenutno na akciji
# s obzirom da su rezultati skriveni iza dugmeta Show more, radim import Seleniuma, radi klikanja spornog dugmeta.
# vrijeme izvođenja --> 3-4 min --> nema potrebe za async

time_sleep = 1

# identificiram se kao Chrome browser, jer ću njega kasnije koristiti za automatizaciju klikanja putem Seleniuma
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Accept-Encoding": "*",
    "Connection": "keep-alive"}

data = []
kategorija = []
kategorija_dict = {}


pocetak_vrijeme = time.time()
s = requests.Session()

response = s.get('https://popusti.njuskalo.hr/', headers=headers)
web_page = response.content
soup = BeautifulSoup(web_page, 'html.parser')

# njuškalo mogu pretraživati na 2 načina: preko kategorija ili preko trgovine
# ako idem preko trgovine, onda ne vidim odmah  kategoriju artikla, nego bi morao kliknuti na pojedini proizvod
# zato idem tradicionalnim putem, preko kategorija --> max 3 nivoa
# popunjavam prvi nivo kategorija

kat1 = []
for a in soup.find('div', {'class': 'content'}).find('ul').find_all('a'):
    kat = []
    kat.append('https://popusti.njuskalo.hr' + a['href'])
    kat.append(a.get_text())
    kat.append('')
    kat.append('')
    kat1.append(kat)


#sad idem redom po kategorijama i gledam sve do trećeg nivoa
for k in kat1:
    response = s.get(k[0], headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, 'html.parser')
    try:
        for li2 in soup.find('nav', {'class' : 'nestedListType1 boxSection'}).find('ul', {'class' : 'lvl0'}).find_all('li'):
            kat2 = []
            kat2.append('https://popusti.njuskalo.hr' + li2.a['href'])
            kat2.append(k[1])
            kat2.append(li2.a.get_text())
            kat2.append('')
            
            if kat2[0] not in kategorija_dict: 
                kategorija_dict[kat2[0]]='1'
                kategorija.append(kat2)
                try:
                    for li3 in li2.find('ul', {'class' : 'lvl1'}).find_all('li'):
                        kat3 = []
                        kat3.append('https://popusti.njuskalo.hr' + li3.a['href'])
                        kat3.append(k[1])
                        kat3.append(li2.a.get_text())
                        kat3.append(li3.a.get_text())
                        if kat3[0] not in kategorija_dict: 
                            kategorija_dict[kat3[0]]='1'
                            kategorija.append(kat3)
                except:
                    pass
                    #print('Iznimka: kategorija 3. nivo')
    except:
        pass
        #print('Iznimka: kategorija 2. nivo')


proizvodi = []
URLs = kategorija
br_kat=1


driver = webdriver.Chrome(executable_path = r'./chromedriver')
for url in URLs:
    driver.get(url[0])   #driver.get(url[0])
    try:
        btn_prihvati = driver.find_element(By.ID, 'didomi-notice-agree-button')
        driver.execute_script("arguments[0].click();", btn_prihvati);
    except:
        pass
        #print('Iznimka: dugme prihvati')
    
    # prvi put stisnem dugme show_more
    try:
        while driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div/div[1]/div[3]/button'):
            btn_show_more = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div/div[1]/div[3]/button')    
            driver.execute_script("arguments[0].click();", btn_show_more);
            time.sleep(time_sleep)
    except:
        pass
        #print('Iznimka: dugme show_more')

    # pokušavam n-ti put stisnuti dugme show_more
    try:
        while driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div/div[1]/div[3]/ul/button'):
            btn_show_more_ul = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div/div[1]/div[3]/ul/button')    
            driver.execute_script("arguments[0].click();", btn_show_more_ul);
            time.sleep(time_sleep)
    except:
        pass
        #print('Iznimka: dugme show_more ul')

    response = s.get(url[0], headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, 'html.parser')

    for div in soup.find_all('div', { 'class' : 'productItemType1 cf offer' }):
        proizvod = []
        poveznica = str(div.find('div', {'class' : 'infoCont'}).a['href'])
        poveznica = 'https://popusti.njuskalo.hr' + poveznica
        kategorija1 = url[1]
        kategorija2 = url[2]
        kategorija3 = url[3]
        trgovina = str(div.find('div', {'class' :'validInfo'}).a.text)
        naziv_proizvoda = str(div.find('div', {'class' : 'infoCont'}).a.text).strip()
        if div.find('div', {'class' :'prices'}).find('p', {'class' :'oldPrice'}) is not None:
            stara_cijena = div.find('div', {'class' :'prices'}).find('p', {'class' :'oldPrice'}).get_text()
            stara_cijena = str(stara_cijena[: stara_cijena.find(' ')].replace(",","."))
        if div.find('div', {'class' :'prices'}).find('p', {'class' :'newPrice'}) is not None:
            nova_cijena = div.find('div', {'class' :'prices'}).find('p', {'class' :'newPrice'}).get_text()
            nova_cijena = str(nova_cijena[: nova_cijena.find(' ')].replace(",","."))
        proizvod.append(poveznica)
        proizvod.append(kategorija1)
        proizvod.append(kategorija2)
        proizvod.append(kategorija3)
        proizvod.append(trgovina)
        proizvod.append(naziv_proizvoda)
        proizvod.append(stara_cijena)
        proizvod.append(nova_cijena)
        proizvodi.append(proizvod)
    print ('Broj kategorije: ' + str(br_kat) + ' / ' + str(len(URLs)))
    br_kat += 1

proizvodi.insert(0, ['poveznica','kategorija1','kategorija2','kategorija3','trgovina','naziv','stara_cijena','nova_cijena'])
with xlsxwriter.Workbook('Njuskalo_popusti.xlsx') as workbook:
    worksheet = workbook.add_worksheet()
    for row_num, proizvodi in enumerate(proizvodi):
        worksheet.write_row(row_num, 0, proizvodi)

kraj_vrijeme = time.time()
ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
print(ukupno_vrijeme)