from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json

# Set up the service for ChromeDriver
service = Service(ChromeDriverManager().install())

# Initialize the Chrome WebDriver with the service
driver = webdriver.Chrome(service=service)

# URL of the fish listing page
listing_url = 'https://www.fishkeeper.co.uk/fish/marine/fish'

# Open the page
driver.get(listing_url)

# Initialize a set to store unique fish names and URLs
fish_names = set()
fish_urls = []

scroll_pause_time = 3  # Pause time between scrolls

while True:
    # Scroll down by smaller increments to ensure all elements load
    driver.execute_script("window.scrollBy(0, 600);")
    
    # Wait for a short time to allow new elements to load
    time.sleep(scroll_pause_time)
    
    # Recheck all fish elements on the page
    fish_elements = driver.find_elements(By.CLASS_NAME, 'data-card__name')
    fish_links = driver.find_elements(By.CSS_SELECTOR, 'a.data-card')
    
    # Add any new fish names and their links to the set
    new_names_added = False
    for fish, link in zip(fish_elements, fish_links):
        if fish.text not in fish_names:
            fish_names.add(fish.text)
            fish_urls.append(link.get_attribute('href'))
            new_names_added = True
    
    # If no new names are added, and we've scrolled to the bottom, break the loop
    new_height = driver.execute_script("return document.body.scrollHeight")
    last_height = driver.execute_script("return window.pageYOffset + window.innerHeight")
    
    if last_height == new_height and not new_names_added:
        break

# Initialize an empty list to store fish details
fish_data = []

# Now, visit each fish's detail page to scrape detailed information
for index, url in enumerate(fish_urls):
    driver.get(url)
    print(f"\nScraping details for fish {index + 1}/{len(fish_urls)}: {url}")
    
    fish_details = {}
    
    # Wait for the Overview section to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'data-view__title'))
        )
        
        # Scrape the fish name (confirming we're on the right page)
        fish_name = driver.find_element(By.CLASS_NAME, 'data-view__description').text.strip()
        fish_details['name'] = fish_name
        
        # Scrape the Overview section (key details)
        overview_table = driver.find_element(By.CLASS_NAME, 'data-view__table')
        rows = overview_table.find_elements(By.TAG_NAME, 'tr')
        overview_details = {}
        for row in rows:
            label = row.find_element(By.TAG_NAME, 'td').text.strip()
            value = row.find_element(By.CLASS_NAME, 'italic-style').text.strip() if 'italic-style' in row.get_attribute('class') else row.find_elements(By.TAG_NAME, 'td')[1].text.strip()
            overview_details[label] = value
        
        fish_details['overview'] = overview_details
        
        # Scrape the Description section
        try:
            description_section = driver.find_element(By.ID, 'care')
            description_text = description_section.text.strip()
            fish_details['description'] = description_text
        except:
            fish_details['description'] = "No description found."
        
        # Scrape the Feeding section
        try:
            feeding_section = driver.find_element(By.ID, 'feeding')
            feeding_text = feeding_section.text.strip()
            fish_details['feeding'] = feeding_text
        except:
            fish_details['feeding'] = "No feeding details found."
        
        # Scrape the Breeding section
        try:
            breeding_section = driver.find_element(By.ID, 'breeding')
            breeding_text = breeding_section.text.strip()
            fish_details['breeding'] = breeding_text
        except:
            fish_details['breeding'] = "No breeding details found."
        
        # Append the fish details to the list
        fish_data.append(fish_details)
        
    except Exception as e:
        print(f"Failed to scrape details for {url}: {e}")
    
    # Wait a bit before moving to the next fish to avoid overwhelming the server
    time.sleep(2)

# Save the fish data to a JSON file
with open('fish_data.json', 'w') as json_file:
    json.dump(fish_data, json_file, indent=4)

print("Data has been saved to fish_data.json")

# Close the browser
driver.quit()