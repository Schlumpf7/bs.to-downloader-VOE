import subprocess
import base64
import requests
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def resolve(url, *, driver=None):
    """
    Returns the URL to the HLS Media Playlist (.m3u8 file).
    """

    if driver is None:
        options = webdriver.ChromeOptions()
        options.add_argument("--incognito")
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

    if isinstance(url, list):
        return [resolve(url, driver=driver) for url in url]

    print(f"Resolving (voe): {url}")

    # Navigate to the URL
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)

    # Waiting for a random large element (e.g., "sprite-plyr") to ensure that the HLS script has finished loading
    wait = WebDriverWait(driver, 10)
    try:
        # Wait for the element with ID 'sprite-plyr' to be present on the page
        wait.until(EC.presence_of_element_located((By.ID, "sprite-plyr")))
    except TimeoutException:
        print("Timeout: The element #sprite-plyr did not appear in time.")
        return None

    # Once the element is found, extract the page source and process it
    return _extract(driver.page_source)

def _extract(html):
    try:
        # Extracting the HLS URL (encoded in base64)
        hls = html.split("\'hls\'")[1]
        hls = hls.split("\'")[1]
        source = base64.b64decode(hls).decode("UTF-8", errors="ignore")
        print(f"Decoded source: {source[:500]}")
    except (IndexError, ValueError) as e:
        print("Error extracting HLS source:", e)
        return None

    # Fetch the master playlist and extract the base URL
    master = requests.get(source).content.decode("UTF-8")
    prefix = source.replace(source.split("/")[-1], "")  # Get the base URL for the HLS segments

    # Return the link to the HLS master playlist (m3u8)
    return prefix + master.split("\n")[2]

def convert_to_mp4(m3u8_url, output_file):
    """
    Use ffmpeg to convert the m3u8 URL to an mp4 file.
    """
    result = subprocess.run([
        "ffmpeg", "-y", "-i", m3u8_url, "-acodec", "copy", "-vcodec", "copy",
        "-hide_banner", "-loglevel", "error", str(output_file)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg-Fehler: {result.stderr}")
        return False

    print(f"Conversion to MP4 successful: {output_file}")
    return True
