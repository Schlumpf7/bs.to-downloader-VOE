# bs.to-downloader

A tool to download entire seasons from bs.to

## Requirements

- python `winget install python`
- pip:
    1. download https://bootstrap.pypa.io/get-pip.py
    *(right-click, save link as)*
    2. `py get-pip.py`
- chromedriver <https://chromedriver.chromium.org>
(or just have chrome installed)
- beautifulsoup4 `pip install beautifulsoup4`
- selenium `pip install selenium`
- requests `pip install requests`
- ffmpeg `winget install ffmpeg`
(for converting the videos to mp4)

## Getting started

1. Visit [bs.to](https://bs.to) and select your desired series (including season and language). Copy the URL in the top bar of your browser (Should be of this form: `http://bs.to/serie/<series>/<season>/<language>`, e.g. `https://bs.to/serie/Downton-Abbey/1/en`).

3. Run the program in the command-line: 
`python . <url>`


## Please note

- Currently only one host ([voe](https://voe.sx)) is supported!

- The download is rather slow due to lack of multithreading



## How it works

This tool uses selenium to parse and query html. It uses chromedriver to control a Chrome browser instance. It opens all episodes on bs.to in your own browser; Conveniently this allows **you** to solve the CAPTCHAs and copy the host-urls, this is (very sadly) necessary sinde bs.to employs CAPTCHAs to protect against browser automation.

The Tool then downloads all parts for the HLS playlist for each episode(this will take a while) and uses ffmpeg to convert them to MP4

## Disclaimer

Use of this tool is at each users own risk. Under no circumstances shall the developer(s) be liable for and indirect, incidental, consequential, special or exemplary damages arising out of the services this tool provides.
