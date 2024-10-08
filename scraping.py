import time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Install the appropriate version of chromedriver
chromedriver_autoinstaller.install()

# Set up Selenium Chrome driver options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless mode (without GUI)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Create a new Selenium driver instance
driver = webdriver.Chrome(service=Service(), options=chrome_options)

def scrape_url(url:str):
    # Open the URL in the browser
    driver.get(url)

    # Wait for the JavaScript to load
    time.sleep(0.1)  # Adjust time as needed based on your connection and website loading time

    # Get the page source after rendering
    page_source = driver.page_source

    # Close the Selenium driver
    # driver.quit()

    # Parse the rendered page source with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract text content from the parsed HTML
    text_content = soup.get_text(separator=' ', strip=True)

    return text_content,soup
