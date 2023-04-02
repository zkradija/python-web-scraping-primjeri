from datetime import datetime
import time
import xlsxwriter
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By


# zadatak: sa internet stranice https://njuskalo.hr skinuti oglase za sve rabljene autombile na električni pogon
# staviti filter na rabljena vozila, cijena barem 5.000 € (mičem slupane), godina proizvodnje >=2011
# s obzirom da su rezultati skriveni iza dugmeta SLJEDEĆA, radim import Seleniuma, radi klikanja spornog dugmeta.
# vrijeme izvođenja --> 3-4 min --> nema potrebe za async

#nema puno strujića pu ću učitati sve županije odjednom
url = 'https://www.njuskalo.hr/rabljeni-auti?onlyFullPrice=1&price%5Bmin%5D=5000&yearManufactured%5Bmin%5D=2011&fuelTypeId=1226&condition%5Btest%5D=1&condition%5Bused%5D=1&sort=cheap'


# identificiram se kao Chrome browser, jer ću njega kasnije koristiti za automatizaciju klikanja putem Seleniuma
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Accept-Encoding": "*",
    "Connection": "keep-alive"}

pocetak_vrijeme = time.time()
s = requests.Session()


response = s.get(url, headers=headers)
web_page = response.content
soup = BeautifulSoup(web_page, 'html.parser')

driver = webdriver.Chrome(executable_path = r'./chromedriver')
driver.get(url)
try:
    btn_prihvati = driver.find_element(By.ID, 'didomi-notice-agree-button')
    driver.execute_script("arguments[0].click();", btn_prihvati);
except:
    pass
    #print('Iznimka: dugme prihvati')

#prvo kupim oglase s prve stranice
# njuškalo gura VauVau oglase. div VauVau oglasa ima sličan naziv  kao div običnih oglasa
# stoga u igru ubacujem etree --> gađam točno div koji želim, i njegove ul/li

# print(driver.find_element(By.XPATH, '/html/body/div[11]/div[3]/div[1]/main/form/div/div[1]/div[4]/div[7]').getText())

try:
    for li in soup.find_all('li', {'class': lambda x: x and x.startswith('EntityList-item EntityList-item--Regular EntityList-item--')}):
        print(li)
except:
    pass

# links = ['','']
# for div in soup.find_all('div'): 
#     print(div.get('class'))
# #    startswith(' EntityList-item EntityList-item--Regular EntityList-item'):
# #        print (li)
#     #links[0] = li.find('a')['href']
#     #links[1] = li.find('a').get_text()

# a onda pokrećem petlju
# try:
#     driver.find_element(By.XPATH, '//*[@id="form_browse_detailed_search"]/div/div[1]/div[4]/div[1]/nav/ul/li[8]/button').click()
# except:
#     pass



