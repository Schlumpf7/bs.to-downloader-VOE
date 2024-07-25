import base64
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def resolve(url, *, driver=None):
    if driver is None:
        options = webdriver.ChromeOptions()
        options.add_argument("--incognito")
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

    if isinstance(url, list):
        return [resolve(url, driver=driver) for url in url]

    print(f"Resolving (voe): {url}")

    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)

    #Waiting for a random big element so the script for getting the hls-source will be finisched
    #if you know how to wait for the script explicitely, please change this
    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.presence_of_element_located((By.ID, "sprite-plyr"))
    )
    return _extract(driver.page_source)


def _extract(html):
    soup = BeautifulSoup(html, "html.parser")

    script = str(soup.find_all("script")[11])
    hls=script.split("\'hls\'")[1]
    hls=hls.split("\'")[1]
    source=base64.b64decode(hls)
    return source
