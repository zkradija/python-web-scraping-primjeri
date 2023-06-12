from bs4 import BeautifulSoup
import requests
import xlsxwriter
import math
from datetime import datetime
import time


# zadatak: sa intrnet stranice https://Posta.hr skinuti sva mjesta, poštanske urede i županije
# prosječno vrijeme 120 sekundi

#identificiram se kao Firefox browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/111.0.1",
    "Accept-Encoding": "*",
    "Connection": "keep-alive"}

url_base='https://www.posta.hr/pretrazivanje-mjesta-s-pripadajucim-postanskim-brojem/1403?pojam=&page='

data=[]

start_time = time.perf_counter()
s = requests.Session()

# prvo tražim broj rezultata, koji dijelim s 20 (rezultata po stranici) --> tako dobijem zadnju stranicu
response = s.get(f'{url_base}1', headers=headers)
web_page = response.content
soup = BeautifulSoup(web_page, 'html.parser')

last_page_text = soup.find('div', attrs={'class':'results-found'}).get_text()
last_page_list = [int(x) for x in last_page_text.split() if x.isdigit()]    # tražim samo brojeve, unutar teksta
last_page = math.ceil((int(last_page_list[0])/20))  # dijelim sa 20 rezultata po stranici, te zaokružujem na broj više

print(f'Zadnja stranica pronađena: {last_page} --> {datetime.now().strftime("%H:%M:%S")} h')

for i in range (1, last_page+1):
    response = s.get(f'{url_base}i', headers=headers)
    web_page = response.content
    soup = BeautifulSoup(web_page, 'html.parser')
    table = soup.find('table', attrs={'class':'tablica-borders'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele]) # rješavam se praznih redova
    if i != 0 and (i == 1 or i % 50 == 0): print(f'Stranica broj: {i} / {last_page} --> {datetime.now().strftime("%H:%M:%S")} h')


# rješavam se praznih polja
data2 = [x for x in data if x]

with xlsxwriter.Workbook('Poštanski_brojevi_html.xlsx') as workbook:
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, 'mjesto')
    worksheet.write(0, 1, 'postanski_ured')
    worksheet.write(0, 2, 'zupanija')
    for row_num, data2 in enumerate(data2):
        worksheet.write_row(row_num + 1, 0, data2)
end_time = time.perf_counter()
elapsed_time = int(end_time) - int(start_time)
print(elapsed_time)
