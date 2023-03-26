from bs4 import BeautifulSoup, SoupStrainer
import requests
import xlsxwriter
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# NIJE GOTOVO - A KAKO STVARI STOJE NITI NEĆE
# KORIŠTENJEM VIŠENITNOG NAČINA RADA PREBRZO SE ŠALJU UPITI NA SERVER PA SERVER JAVLJA:
# Request blocked. We can't connect to the server for this app or website at this time. There might be too much traffic or a configuration error. Try again later, or contact the app or website owner.
# If you provide content to customers through CloudFront, you can find steps to troubleshoot and help prevent this error by reviewing the CloudFront documentation.
#
# kasnije ću isprobat s timerima malo usporiti program

# zadatak: sa intrnet stranice https://Konzum.hr skinuti sve proizvode s pripadajućim cijenama
# cijene ćemo preuzeti sa stranice kategorija, gdje su navedeni proizvodi pojedine kategorije. ne treba otvarati stranicu pojedinačnog proizvoda
# sada koristim asinkroni način rada, točnije koristiti ću 12 nit (Amd 3600 6 jezgri sa 12 niti)
# html_async --> prosječno vrijeme 330 sekundi

#identificiram se kao Firefox browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Accept-Encoding": "*",
    "Connection": "keep-alive"}

data=[]
kategorija = []

pocetak_vrijeme = time.time()
s = requests.Session()



response = s.get('https://www.konzum.hr/kreni-u-kupnju', headers=headers)
web_page = response.content
soup = BeautifulSoup(web_page, 'html.parser')

for a in soup.find_all('a', {'class': 'category-box__link'}):
    kat1 = []
    if str(a['href']).startswith('/web/'):
        kat1.append('https://konzum.hr' + a['href'])
        kat1.append(str(a.find('h3', {'class':'category-box__title'}).get_text()))
        kategorija.append(kat1)


#sada tražim kategorije po nivoima  - znam da ima max 3 lvla (nav-child-wrap-level-3)
#prvo idem nivo 2
for ul in soup.find_all('ul', {'class' : 'nav-child-wrap-level-2'}):
    kat2 = []
    kat2.append ('https://konzum.hr' + ul.a['href'])
    kat2.append (str(ul.a.get_text()).strip())
    kategorija.append(kat2)

#a onda nivo 3    
for ul in soup.find_all('ul', {'class' : 'nav-child-wrap-level-3'}):
    for li in ul.find_all('li'):
        kat3 = []
        if li.a is not None:
            kat3.append ('https://konzum.hr' + li.a['href'])
            kat3.append (str(li.a.get_text()).strip())
            kategorija.append(kat3)


#čistim kategorije od glavnih kategorija. zanimaju me samo najniži nivoi
i=0
br=len(kategorija)-1
while br>0:
    x = str(kategorija[i][0])
    y = kategorija[i+1][0]

    if y.startswith(x): 
        del kategorija[i]
    else:
        i+=1
    br-=1

print('Kategorije pronađene: ' + time.strftime('%H:%M:%S') + ' h')

#brojac koristim radi izračuna brzine
brojac=1
#krećem listanje proizvoda po kategorijama
t = time.localtime()
print('Proizvod broj ' + str(brojac) + ' u ' + str(time.strftime("%H:%M:%S", t)))

URLs = kategorija

def parse(url):
    response = requests.get(url[0], headers=headers)
    web_page = response.content
    only_article_tags=SoupStrainer('article')   #gledam samo article, radi ubrzanja
    soup = BeautifulSoup(web_page, 'html.parser', parse_only=only_article_tags)
    for article in soup.find_all('article'):
        proizvod = []
        if article is not None: 
            proizvod.append ('https://konzum.hr' + str(article.find('a', {'class' : 'link-to-product'})['href']))
            proizvod.append (url[1])
            proizvod.append (str(article.div.attrs['data-ga-id']))
            proizvod.append (str(article.div.attrs['data-ga-name']))
            proizvod.append (float(article.div.attrs['data-ga-price'].replace(" €","").replace(",",".")))    #prvo mičem oznaku €, zatim pretvaram decimalni zarez u točku, da bi na kraju pretvorio u broj
            return proizvod

    
if __name__ == '__main__':
    with ProcessPoolExecutor(max_workers=12) as executor:
        futures = [ executor.submit(parse, url) for url in URLs ]
        for result in as_completed(futures):
            brojac+=1
            #ispisujem svaki 500ti da vidim brzinu            
            if brojac %500 == 0: 
                t = time.localtime()
                print('Proizvod broj ' + str(brojac) + ' u ' + str(time.strftime("%H:%M:%S", t)))
            data.append(result)


    # #ubacujem nazive stupaca, radi prebacivanja u Excel
    data.insert(0, ['poveznica','kategorija','sifra','naziv','cijena_EUR_kom'])

    with xlsxwriter.Workbook('Konzum_html_async.xlsx') as workbook:
        worksheet = workbook.add_worksheet()
        for row_num, data in enumerate(data):
            worksheet.write_row(row_num, 0, data)

    kraj_vrijeme = time.time()
    ukupno_vrijeme=kraj_vrijeme-pocetak_vrijeme
    print(ukupno_vrijeme)
