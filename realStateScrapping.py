import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import re


options = Options()
options.add_argument("--headless")  # Enable headless mode explicitly


# Initialize the Chrome WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def get_href_links(url):
    """Retrieve all href links from the given URL."""
    driver.get(url)
    time.sleep(5)  # Wait for page to load
    elements = driver.find_elements(By.CSS_SELECTOR, 'div.sc-1dun5hk-0.cOiOrj a')
    href_links = [element.get_attribute('href') for element in elements]
    return href_links

def get_property_data(url, retries=3):
    """Retrieve property data from the given URL with retry logic."""
    for attempt in range(retries):
        try:
            driver.get(url)
            time.sleep(5)  # Wait to ensure the page has loaded completely
            
            data = {}
            # Property Type
            try:
                data['Property Type'] = driver.find_element(By.XPATH, "//div[contains(@class, 'propertyTypes')]//div[contains(@class, 'basicInfoValue')]").text
            except:
                data['Property Type'] = None

            # Listing Status
            try:
                data['Listing Status'] = driver.find_element(By.XPATH, "//div[contains(@class, 'status')]//div[contains(@class, 'basicInfoValue')]").text
            except:
                data['Listing Status'] = None

            # Building Size
            try:
                building_size_element = driver.find_element(By.XPATH, "//div[contains(@class, 'hMXWVZ') and .//div[contains(text(), 'Building Size')]]//div[contains(@class, 'basicInfoValue')]")
                building_size_text = building_size_element.text.strip()
                match = re.search(r'(\d+(\.\d+)?)', building_size_text)
                data['Building Size(sq. m)'] = match.group(1) if match else None
            except:
                data['Building Size(sq. m)'] = None

            # Year Built
            try:
                data['Year Built'] = driver.find_element(By.XPATH, "//div[contains(@class, 'yearBuilt')]//div[contains(@class, 'basicInfoValue')]").text
            except:
                data['Year Built'] = None

            # Rooms
            try:
                rooms_text = driver.find_element(By.XPATH, "//div[contains(@class, 'rooms')]//div[contains(@class, 'basicInfoValue')]").text
                rooms_split = rooms_text.split(', ')
                data['Bedrooms'] = [int(s.split()[0]) for s in rooms_split if 'bedroom' in s][0]
                data['Bathrooms'] = [int(s.split()[0]) for s in rooms_split if 'bathroom' in s][0]
            except:
                data['Bedrooms'] = data['Bathrooms'] = None

            # Num Floors
            try:
                data['Num Floors'] = driver.find_element(By.XPATH, "//div[contains(@class, 'numFloors')]//div[contains(@class, 'basicInfoValue')]").text
            except:
                data['Num Floors'] = 0

            # Address
            try:
                address_element = driver.find_element(By.XPATH, "//h1[@class='display-address']")
                full_address = address_element.text.strip()
                
                # Extract City, State, and ZIP Code
                match = re.search(r",\s*([^,]+?),\s*([A-Z]{2})\s*(\d{5})$", full_address)
                if match:
                    data['City'] = match.group(1)
                    data['State'] = match.group(2)
                    data['ZIP Code'] = match.group(3)
                else:
                    data['City'] = None
                    data['State'] = None
                    data['ZIP Code'] = None

            except:
                data['Full Address'] = None
                data['City'] = None
                data['State'] = None
                data['ZIP Code'] = None

            # USD Price
            try:
                price_element = driver.find_element(By.XPATH, "//div[@class='sc-10v3xoh-1 cqrlhJ']")
                price_text = price_element.text.strip()
                match = re.search(r'(\d+[\d,]*)', price_text)
                data['USD Price'] = match.group(1) if match else None
            except:
                data['USD Price'] = None

            return data
        
        except:
            time.sleep(random.uniform(2, 5))  # Wait a random short duration before retrying
    
    return None

def main():
    # Define the base URLs for each state
    base_urls = {
       'idaho': 'https://www.realestate.com.au/international/us/idaho',
       'south-dakota' : 'https://www.realestate.com.au/international/us/south-dakota',
       'north-dakota' : 'https://www.realestate.com.au/international/us/north-dakota',
       'montana' : 'https://www.realestate.com.au/international/us/montana',
       'wyoming': 'https://www.realestate.com.au/international/us/wyoming'
    }

    # Define the CSV file path and write the header
    csv_file = r'C:\Users\ankit\Downloads\PowerBI\idaho\idahoreal_estate_data1.csv'
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Property Type', 'Listing Status', 'Building Size(sq. m)', 'Year Built', 
                         'Bedrooms', 'Bathrooms', 'Num Floors', 'City', 'State', 'ZIP Code', 'USD Price'])

        for state, base_url in base_urls.items():
            
            for page in range(1, 161):  # Iterate through pages 1 to 160
                print(f'Scrapping for Page {page}')
                page_url = f"{base_url}/p{page}?searchtypes=townhouse+house"
                
                href_links = get_href_links(page_url)
                
                # Process each link one by one
                for link in href_links:
                    if link:  # Check if the link is valid
                        property_data = get_property_data(link)
                        if property_data:  # Only write data if it was successfully retrieved
                            property_data['State'] = state  # Add state information

                            # Write the property data to the CSV file
                            writer.writerow([
                                property_data.get('Property Type'),
                                property_data.get('Listing Status'),
                                property_data.get('Building Size(sq. m)'),
                                property_data.get('Year Built'),
                                property_data.get('Bedrooms'),
                                property_data.get('Bathrooms'),
                                property_data.get('Num Floors'),
                                property_data.get('City'),
                                property_data.get('State'),
                                property_data.get('ZIP Code'),
                                property_data.get('USD Price')
                            ])
                        else:
                            print(f"Skipping link due to error: {link}")
            print(f"Completed scraping for {state}")
    
    driver.quit()

if __name__ == "__main__":
    main()