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


# zadatak: sa internet stranice https://njuskalo.hr skinuti oglase za sve rabljene autombile na električni pogon
# staviti filter na rabljena vozila, cijena barem 5.000 € (mičem slupane), godina proizvodnje >=2011
# s obzirom da su rezultati skriveni iza dugmeta SLJEDEĆA, radim import Seleniuma, radi klikanja spornog dugmeta.
# vrijeme izvođenja --> 3-4 min --> nema potrebe za async

#nema puno strujića pu ću učitati sve županije odjednom
url = 'https://www.njuskalo.hr/rabljeni-auti?onlyFullPrice=1&price%5Bmin%5D=5000&yearManufactured%5Bmin%5D=2011&fuelTypeId=1226&condition%5Btest%5D=1&condition%5Bused%5D=1&sort=cheap'


# identificiram se kao Chrome browser, jer ću njega kasnije koristiti za automatizaciju klikanja putem Seleniuma
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5112.79 Safari/537.36',
    'Accept-Encoding': '*',
    'Connection': 'keep-alive'}

time_sleep = 0.5
pocetak_vrijeme = time.time()
s = requests.Session()


driver = webdriver.Chrome(executable_path = r'./chromedriver')
driver.get(url)
driver.find_element(By.ID, 'didomi-notice-agree-button').click()

URLs = []

while driver.find_element(By.CSS_SELECTOR, 'button.Pagination-link.js-veza-stranica'):    
    links = driver.find_elements(By.XPATH, '//a[@href]')
    for a in links:
        # print(a.get_attribute('href'))
        if a.get_attribute('href').startswith('https://www.njuskalo.hr/auti/'):
            URLs.append('https://njuskalo.hr' +  a.get_attribute('href'))
    
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    for button in buttons:
        print(button.text.strip()[:8])
        if button.text.strip()[8:] == 'SLJEDEĆA':
            button.click()
            break;
    print(URLs)    
    #driver.find_element(By.CSS_SELECTOR, 'button.Pagination-link.js-veza-stranica').click()

print(URLs)




# for url in URLs:
#     time.sleep(time_sleep)
#     response = s.get(url,headers=headers)
#     web_page = response.content
#     soup = BeautifulSoup(web_page, "html.parser")

#     # prvo radim kontrolu radi li se o eletričnom autu
#     el_auto = 0
#     for ul in soup.find_all('div'):
#         print(ul)    
    #     if li.find('dd', _class='ClassifiedDetailHighlightedAttributes-text') == 'Električni':
    #          el_auto = 1

    # if el_auto == 1:
    #     print('je')
#    if root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[4]/ul/li[4]/dl/dd')[0] == 'Električni':



#     r = s.get(url + str(i), headers=headers)
#     root = lxml.html.fromstring(r.content)
#     # filter za električne aute, jer je na početku bilo oglasa s autima koji nisu električni
#     oglas = ['','','','','','','']
#     a = root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[4]/ul/li[4]/dl/dd')
#     print (a)
#     print(root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[4]/ul/li[4]/dl/dd')[1])
#     if root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[4]/ul/li[4]/dl/dd')[0] == 'Električni':
#         oglas[0] = url + str(i) # poveznica
#         oglas[1] = root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[2]/div[2]/div[1]/h1').text[0]   # naslov
#         cijena_txt = root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[2]/div[2]/div[2]/div[1]/dl/dd').text[0]
#         oglas[2] = int(cijena_txt.split('€').strip().replace('.',''))    # cijena
#         oglas[3] = int(root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[4]/ul/li[1]/dl/dd').text[0])   # godina proizvodnje
#         km_txt = root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[4]/ul/li[2]/dl/dd').text[0]
#         oglas[4] = km_txt.strip().replace('.','')  # kilometraža
#         snaga_motora_txt = root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[4]/ul/li[3]/dl/dd').text[0]
#         oglas[5] = int(snaga_motora_txt.strip())    # snaga motora
#         oglas[6] = root.xpath('/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[5]/dl/dd[2]/span').text[0]   # marka
# #        oglas[7] =/html/body/div[6]/div[3]/main/article/div[1]/div/div[1]/div[5]/dl/dd[3]/span
        # oglasi.append(oglas)

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



