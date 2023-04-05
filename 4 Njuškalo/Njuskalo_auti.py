from datetime import datetime
import time
import xlsxwriter
from bs4 import BeautifulSoup
import requests
import random
import lxml.html
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pprint

# zadatak: sa internet stranice https://njuskalo.hr skinuti oglase za sve rabljene autombile na električni pogon
# staviti filter na ELEKTRIČNA rabljena vozila, cijena barem 5.000 € (mičem slupane), godina proizvodnje >=2011
# vrijeme izvođenja --> 7-8 min

url_baza = 'https://www.njuskalo.hr/rabljeni-auti?onlyFullPrice=1&price%5Bmin%5D=5000&yearManufactured%5Bmin%5D=2011&fuelTypeId=1226&condition%5Btest%5D=1&condition%5Bused%5D=1&sort=cheap&page='


options = Options()
options.page_load_strategy = 'eager'    # čekam da se učitaju DOM lementi, ne zanima me ništa drugo


pocetak_vrijeme = time.time()


url = url_baza + str(1)
driver = webdriver.Chrome(executable_path = r'./chromedriver',options=options)
driver.get(url)
driver.find_element(By.ID, 'didomi-notice-agree-button').click()

broj_oglasa = int(driver.find_element(By.CLASS_NAME, 'entities-count').text)
last_page = math.ceil(broj_oglasa / 25)

URLs = []
urls_dict = {}  # za obranu od duplića


for i in range (1, last_page + 1):
    url = url_baza + str(i)
    driver.get(url)
    links = driver.find_elements(By.XPATH, '//a[@href]')
    for a in links:
        # print(a.get_attribute('href'))
        if a.get_attribute('href').startswith('https://www.njuskalo.hr/auti/'):
            if a.get_attribute('href') not in urls_dict:    
                urls_dict[a.get_attribute('href')] = '1'
                URLs.append(a.get_attribute('href'))


driver.quit()
options.add_argument('--headless=new')
options = Options()
options.page_load_strategy = 'eager'
driver = webdriver.Chrome(executable_path = r'./chromedriver',options=options)


oglasi = []

for url in URLs:
    driver.get(url)


    # prvo radim kontrolu radi li se o eletričnom autu
    el_auto = 0

    for d in driver.find_elements(By.CLASS_NAME, 'ClassifiedDetailHighlightedAttributes-text'):
        #print(d.text)
        if d.text == 'Električni':
            el_auto = 1

    
    if el_auto == 1:
        oglas = ['','','','','','','','','']
        oglas[0] = url  #poveznica
        oglas[1] = driver.find_element(By.CLASS_NAME, 'ClassifiedDetailSummary-title').text # naslov oglasa
        oglas[2] = driver.find_element(By.CLASS_NAME, 'ClassifiedDetailSummary-priceDomestic').text.split('€')[0].strip().replace('.','')  # cijena
        for dt in driver.find_elements(By.CLASS_NAME, 'ClassifiedDetailBasicDetails-listTerm'):
            match dt.text:
                case 'Marka automobila': oglas[3] = dt.find_element(By.XPATH, './following-sibling::dd').text
                case 'Model automobila': oglas[4] = dt.find_element(By.XPATH, './following-sibling::dd').text
                case 'Tip automobila': oglas[5] = dt.find_element(By.XPATH, './following-sibling::dd').text
                case 'Godina proizvodnje': oglas[6] = dt.find_element(By.XPATH, './following-sibling::dd').text.split('.')[0]
                case 'Prijeđeni kilometri': oglas[7] =  dt.find_element(By.XPATH ,'./following-sibling::dd').text.split(' ')[0].strip().replace('.','')
                case  'Snaga motora': oglas[8] =  dt.find_element(By.XPATH, './following-sibling::dd').text.split(' ')[0].strip()
        oglasi.append(oglas)

driver.quit()

oglasi.insert(0, ['poveznica','naslov_oglasa','cijena','marka','model','tip','godina_proizvodnje','km','snaga_motora'])
with xlsxwriter.Workbook('Njuskalo_auti.xlsx') as workbook:
    worksheet = workbook.add_worksheet()
    for row_num, oglasi in enumerate(oglasi):
        worksheet.write_row(row_num, 0, oglasi)


kraj_vrijeme = time.time()
ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
print(ukupno_vrijeme)