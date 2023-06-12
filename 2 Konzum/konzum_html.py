from bs4 import BeautifulSoup, SoupStrainer
import requests
import xlsxwriter
import time


# zadatak: sa internet stranice https://Konzum.hr skinuti sve proizvode s pripadajućim cijenama (cca 6.100 proizvoda)
# cijene ćemo preuzeti sa stranice kategorija, gdje su navedeni proizvodi, pojedine kategorije. ne treba otvarati stranicu pojedinačnog proizvoda
# koristim html pasrser
# prosječno vrijeme rada 220 sekundi

# identificiram se kao Firefox browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/111.0.1",
    "Accept-Encoding": "*",
    "Connection": "keep-alive"}

products = []
categories = []

start_time = time.perf_counter()
s = requests.Session()

response = s.get('https://www.konzum.hr/kreni-u-kupnju', headers=headers)
web_page = response.content
soup = BeautifulSoup(web_page, 'html.parser')

for a in soup.find_all('a', {'class': 'category-box__link'}):
    cat1 = []
    if str(a['href']).startswith('/web/'):
        cat1.append(f'https://konzum.hr{a["href"]}')
        cat1.append(f'{a.find("h3", {"class": "category-box__title"}).get_text()}')
        cat1.append('1')
        categories.append(cat1)


#sada tražim kategorije po nivoima  - znam da ima max 3 lvla (nav-child-wrap-level-3)
#prvo idem nivo 2
for ul in soup.find_all('ul', {'class' : 'nav-child-wrap-level-2'}):
    cat2 = []
    cat2.append (f'https://konzum.hr{ul.a["href"]}')
    cat2.append (str(ul.a.get_text()).strip())
    cat2.append ('2')
    categories.append(cat2)

#a onda nivo 3    
for ul in soup.find_all('ul', {'class' : 'nav-child-wrap-level-3'}):
    for li in ul.find_all('li'):
        cat3 = []
        if li.a is not None:
            cat3.append (f'https://konzum.hr{li.a["href"]}')
            cat3.append (str(li.a.get_text()).strip())
            cat3.append('3')
            categories.append(cat3)

# sortiram - priprema za brisanje nadkategorija
categories.sort(key=lambda x: x[0])


# čistim kategorije od glavnih kategorija. zanimaju me samo najniži nivoi
i = 0
br=len(categories) - 1
while br > 0:
    x = str(categories[i][0])
    x_kat = int(categories[i][2])
    y = str(categories[i+1][0])

    if y.startswith(x) and x_kat == 1: 
        del categories[i]
    else:
        i+=1
    br-=1


print(f'Kategorije pronađene: {time.strftime("%H:%M:%S")} h')

# brojac koristim radi izračuna brzine
brojac=1

# krećem listanje proizvoda po kategorijama
t = time.localtime()

print(f'Proizvod broj {brojac} u {time.strftime("%H:%M:%S", t)}')

products = []
for category in categories:
    response = s.get(category[0], headers=headers)
    web_page = response.content
    only_article_tags = SoupStrainer('article')   #gledam samo article, radi ubrzanja
    soup = BeautifulSoup(web_page, 'html.parser', parse_only=only_article_tags)

    for article in soup.find_all('article'):
        
        if article is not None: 
            product = [
                f'https://konzum.hr{article.find("a", {"class" : "link-to-product"})["href"]}',
                category[1],
                str(article.div.attrs['data-ga-id']),
                str(article.div.attrs['data-ga-name']),
                float(article.div.attrs['data-ga-price'].replace(' €','').replace(',','.'))
            ]
            products.append(product)
            brojac += 1
            #ispisujem svaki 500-ti da vidim brzinu            
            if brojac %500 == 0: 
                t = time.localtime()
                print(f'Proizvod broj {brojac}  u {time.strftime("%H:%M:%S", t)}')

#ubacujem nazive stupaca, radi prebacivanja u Excel
products.insert(0, ['poveznica','kategorija','sifra','naziv','cijena_EUR_kom'])

with xlsxwriter.Workbook('./2 Konzum/Konzum_html.xlsx') as workbook:
    worksheet = workbook.add_worksheet()
    for row_num, products in enumerate(products):
        worksheet.write_row(row_num, 0, products)

end_time = time.perf_counter()
elapsed_time = int(end_time) - int(start_time)
print(elapsed_time)

