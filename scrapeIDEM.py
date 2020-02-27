import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from itertools import islice
import re
import os
import ctypes

chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
final = []
targetColumns = ['Name', 'License#', 'Profession', 'LicenseType', 'Status', 'Address']
dfFinal = pd.DataFrame(columns = targetColumns)
URL = 'https://mylicense.in.gov/everification/Search.aspx'
driver.get(URL)
driver.implicitly_wait(10)
licenseDD = driver.find_element_by_id('t_web_lookup__license_type_name')
licenseDD.click()
bdtOption = driver.find_element_by_xpath("//select/option[@value='Backflow Device Tester']")
bdtOption.click()
search = driver.find_element_by_id('sch_button')
search.click()
page = 1
maxPage = 40
lastPage = 1000

def scrapeTable() :
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    table = soup.find(id='datagrid_results')
    result = []
    for row in table.find_all('tr') :
        for cell in row.find_all('td') :
            if cell.text == " ":
                print('nothing')
                continue
            result.append(cell.text)
    global pages
    pages = next(reversed(result))
    result = list(filter(('').__ne__, result))
    result.pop()
    delete = []
    for i in result :
        if '\n' in i :
            delete.append(i)
    for i in delete :
        result.remove(i)
    result = np.delete(result, slice(6, None, 7))
    grouped = [result[i:i+6] for i in range(0, len(result), 6)]
    final.append(grouped)

while page <= maxPage :
    print('Getting page ' + str(page))
    scrapeTable()
    if (page > 40 and len(driver.find_elements_by_link_text('...')) == 1) :
        lastPage = pages[-3:]
    if page == int(str(lastPage)) :
        break
    else :
        if page == maxPage :
            elipses = driver.find_elements_by_link_text('...')
            if page == 40 :
                elipses[0].click()
            else :
                elipses[1].click()
            maxPage += 40
            page += 1
            continue
        else :
            nextPage = driver.find_element_by_link_text(str(page+1))
            nextPage.click()
            page += 1
for i in final :
    dfTemp = pd.DataFrame(i, columns = targetColumns)
    dfFinal = dfFinal.append(dfTemp, ignore_index=True)

errorDf = pd.DataFrame(columns = targetColumns)
for i in dfFinal.index :
    if 'BF' not in dfFinal.at[i, 'License#'] :
        errorDf = errorDf.append(dfFinal.loc[i])
cols = errorDf.columns.tolist()
cols = cols[-1:] + cols[:-1]
errorDf = errorDf[cols]
errorDf.rename(columns={'Address': 'Name', 'Name': 'License#', 'License#': 'Profession', 'Profession': 'LicenseType', 'LicenseType': 'Status', 'Status': 'Address'}, inplace=True)
for i in errorDf.index :
    if ',' in errorDf.at[i, 'License#'] or 'Drinking' in errorDf.at[i, 'License#'] :
        errorDf.at[i, 'License#'] = ''
dfFinal.update(errorDf)

print('Finished, saving as testersIDEM.xlsx')
dfFinal.to_excel('testersIDEM.xlsx')
print('Saved! This window can be closed.')
driver.quit()
ctypes.windll.user32.MessageBoxW(0, "Your file is saved as 'testersIDEM.xlsx'", "Done!", 1)