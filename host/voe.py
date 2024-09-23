import base64
import os
import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def resolve(url, *, driver=None):
    """
    Returns a list where the fist element is the Link to the HLS Media Playlist .m3u8 file.
    
    The following elements are the Links to the .ts video files.
    """
    if driver is None:
        options = webdriver.ChromeOptions()
        options.add_argument("--incognito")
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

    if isinstance(url, list):
        return [resolve(url, driver=driver) for url in url]

    print(f"Resolving (voe): {url}")

    #TODO: IGNORE SSL HANDSHAKE
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)


    #Waiting for a random big element so the script for getting the hls-source will be finisched
    #if you know how to wait for the script explicitely, please change this
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(
            EC.presence_of_element_located((By.ID, "sprite-plyr"))
        )
    except TimeoutException:
        return None
    return _extract(driver.page_source)


def _extract(html):
    hls=html.split("\'hls\'")[1]
    hls=hls.split("\'")[1]
    source=base64.b64decode(hls).decode("UTF-8")
    
    master=requests.get(source).content.decode("UTF-8")
    prefix=source.replace(source.split("/")[-1], "")#source minus everything after the last "/"
    #prefix example: https://delivery-node-p85gf9aoh6mefgdf.voe-network.net/engine/hls2-c/01/08273/5h9fug3g4ge2_,n,.urlset/
    
    sources=[prefix+master.split("\n")[2]]#add Media Playlist link to sources list 
    
    mediaPL=requests.get(sources[0]).content.decode("UTF-8")#get media playlist
    #loop over each segment in Media playlist to generate link
    segments=mediaPL.split("\n")[6:]
    for i in range(len(segments)):
        if i%2==0 or i==len(segments)-1: 
            #skip every second line because it just contains the duration of the snippet
            continue 
        
        seg=segments[i]
        sources.append(prefix+seg)#add snippet link to list 
        
    return sources

def download_part(id, m3u8_filename, link):
    local_filename = "./tmp/"+link.split('/')[-1].split("?")[0]
    f=open(local_filename, "wb")
    f.write(requests.get(link).content)
    f.close()


