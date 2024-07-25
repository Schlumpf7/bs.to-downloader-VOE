import utils

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

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, ".stream-content > div > div > video > source")))

    return _extract(driver.page_source)


def _extract(html):
    soup = utils.soup(html)

    # source = soup.select_one(".stream-content > div > div > video > source")
    source = soup.find("source")
    return source["src"], source["type"], source["size"]
