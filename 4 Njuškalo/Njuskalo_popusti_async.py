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
time_sleep = 1

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


URLs = kategorija

for url in URLs:
    response = s.get(url[0], headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, 'html.parser')
    driver = webdriver.Chrome(executable_path = r'./chromedriver')
    driver.get(url[0])
    btn_prihvati = driver.find_element(By.ID, 'didomi-notice-agree-button')
    driver.execute_script("arguments[0].click();", btn_prihvati);
    
'navigation nBtn btnType3 showMore ''

    