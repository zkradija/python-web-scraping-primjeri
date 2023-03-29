from datetime import datetime
import time
import xlsxwriter
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By

# zadatak: sa internet stranice https://Index.hr skinuti sve oglase za automobile (cca 28.000 oglasa)
# filtrirat ćemo oglase - zanimaju nas samo oni oglasi koji imaju popunjena sva željena polja
# cca 5-10x brže radi nego verzija bez ProcessPoolExecutor. može i brže, ali onda se aktivira DDoS zaštita na serveru. zato usporavam sa time.sleep(1)
# workers = 12 / time_sleep = 1.0 sec --> odradi za cca 70 min

workers = 12    # obično se stavlja broj logičkih procesora. napomena: The number of workers must be less than or equal to 61 if Windows is your operating system.
time_sleep = 0.5

# identificiram se kao Firefox browser
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Accept-Encoding": "*",
    "Connection": "keep-alive"}

data = []
kategorija = []


pocetak_vrijeme = time.time()
s = requests.Session()

response = s.get('https://popusti.njuskalo.hr/', headers=headers)
web_page = response.content
soup = BeautifulSoup(web_page, 'html.parser')


for a in soup.find('div', {'class': 'content'}).find('ul').find_all('a'):
    kat = []
    kat.append('https://popusti.njuskalo.hr' + a['href'])
    kat.append(a.get_text())
    kategorija.append(kat)

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
        print('Iznimka: dugme prihvati')
    
    # prvi put stisnem dugme show_more
    try:
        while driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div/div[1]/div[2]/button'):
            btn_show_more = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div/div[1]/div[2]/button')    
            driver.execute_script("arguments[0].click();", btn_show_more);
            time.sleep(time_sleep)
    except:
        print('Iznimka: dugme show_more')

    # pokušavam n-ti put stisnuti dugme show_more
    try:
        while driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div/div[1]/div[2]/ul/button'):
            btn_show_more_ul = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div/div[1]/div[2]/ul/button')    
            driver.execute_script("arguments[0].click();", btn_show_more_ul);
            time.sleep(time_sleep)
    except:
        print('Iznimka: dugme show_more ul')

    response = s.get(url[0], headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, 'html.parser')

    for div in soup.find_all('div', { 'class' : 'productItemType1 cf offer' }):
        proizvod = []
        poveznica = str(div.find('div', {'class' : 'infoCont'}).a['href'])
        poveznica = 'https://popusti.njuskalo.hr' + poveznica
        kategorija = url[1]
        trgovina = str(div.find('div', {'class' :'validInfo'}).a.text)
        naziv_proizvoda = str(div.find('div', {'class' : 'infoCont'}).a.text).strip()
        if div.find('div', {'class' :'prices'}).find('p', {'class' :'oldPrice'}) is not None:
            stara_cijena = div.find('div', {'class' :'prices'}).find('p', {'class' :'oldPrice'}).get_text()
            stara_cijena = str(stara_cijena[: stara_cijena.find(' ')].replace(",","."))
        if div.find('div', {'class' :'prices'}).find('p', {'class' :'newPrice'}) is not None:
            nova_cijena = div.find('div', {'class' :'prices'}).find('p', {'class' :'newPrice'}).get_text()
            nova_cijena = str(nova_cijena[: nova_cijena.find(' ')].replace(",","."))
        proizvod.append(poveznica)
        proizvod.append(kategorija)
        proizvod.append(trgovina)
        proizvod.append(naziv_proizvoda)
        proizvod.append(stara_cijena)
        proizvod.append(nova_cijena)
        proizvodi.append(proizvod)
    print ('Broj kategorije: ' + str(br_kat) + ' / ' + str(len(URLs)))
    br_kat += br_kat

proizvodi.insert(0, ['poveznica','kategorija','sifra','naziv','cijena_EUR_kom'])
with xlsxwriter.Workbook('Njuskalo_popusti.xlsx') as workbook:
    worksheet = workbook.add_worksheet()
    for row_num, proizvodi in enumerate(proizvodi):
        worksheet.write_row(row_num, 0, proizvodi)

kraj_vrijeme = time.time()
ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
print(ukupno_vrijeme)