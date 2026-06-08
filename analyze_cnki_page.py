import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By

def main():
    chromedriver_bin = './chrome-win64/chrome.exe'
    chrome_options = webdriver.ChromeOptions()
    if os.path.exists(chromedriver_bin):
        chrome_options.binary_location = chromedriver_bin
        print("Using provided Chrome binary:", chromedriver_bin)
    else:
        print("Provided Chrome binary not found, using default.")
    
    driver = webdriver.Chrome(options=chrome_options)
    url = "https://co2.cnki.net/Login.html?dp=tute&r=1604392739553"
    print(f"Opening browser to {url} ...")
    driver.get(url)
    
    print("Please ensure your network/VPN is connected and the page is loaded.")
    print("Waiting 15 seconds to allow page to load or for you to connect...")
    for i in range(15):
        time.sleep(1)
        
    print("Dumping HTML to page_source.html...")
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Dump complete. You can close the browser if you want.")
    
    # Wait for an additional 60 seconds just in case user needs to navigate somewhere else and dump again.
    # Actually, we can just quit.
    driver.quit()

if __name__ == '__main__':
    main()
