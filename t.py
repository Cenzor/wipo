
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


co = Options()
proxy = '45.10.167.95:8085'
co.add_argument(f'--proxy-server={proxy}')
co.add_argument('--headless')
driver = webdriver.Chrome('./chromedriver', options=co)
driver.get('https://www3.wipo.int/branddb/en/')
print(driver.page_source)
