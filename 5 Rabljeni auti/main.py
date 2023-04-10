#import index, neostar, dasweltauto, trcz, autohrvatska

import time 
 
import pandas as pd 
from selenium import webdriver 
from selenium.webdriver import Chrome 
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By 
from webdriver_manager.chrome import ChromeDriverManager


def proba():
    # start by defining the options 
    options = webdriver.ChromeOptions() 
#    options.add_argument('--headless')
    options.add_experimental_option( "prefs",{'profile.managed_default_content_settings.javascript': 2})
    options.page_load_strategy = 'none' 
    # this returns the path web driver downloaded 
    chrome_path = ChromeDriverManager().install() 
    chrome_service = Service(chrome_path) 
    # pass the defined options and service objects to initialize the web driver 
    driver = Chrome(options=options, service=chrome_service) 
    #driver.implicitly_wait(5)

    driver.get('https://www.whatismybrowser.com/detect/is-javascript-enabled') 
    driver.get('https://www.trcz.hr/rabljena-vozila-3.aspx?page=2') 

    #print(driver.find_elements(By.TAG_NAME, 'a').text)

    for div in  driver.find_elements(By.TAG_NAME, 'div'):
        print (div.text)        


if __name__ == '__main__':
    proba()
    #index.oglasi()
    #neostar.oglasi()
    #dasweltauto.oglasi()
    #trcz.oglasi()
    #autohrvatska.oglasi()