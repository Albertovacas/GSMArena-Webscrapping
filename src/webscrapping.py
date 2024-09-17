import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import sys,os


class WebScraper:
    """
    Class to perform web scraping on a given website to extract brand and phone links.
    """

    def __init__(self, options) -> None:
        """
        Initialize the WebScraper with the provided WebDriver options.
        """
        self.options = options
        self.brand_page_links = []
        self.phone_page_links = []
        self.phone_df = self._get_phone_df()

    def _fetch_brand_phone_links(self) -> None:
        """
        Recursively fetch phone links from the next pages for each brand.
        """
        driver = webdriver.Chrome(options=self.options)
        for brand in self.brand_page_links:
            print(brand)
            time.sleep(random.uniform(1, 3))  # Random wait to mimic human behavior
            try:
                driver.get(brand)
                next_pages = driver.find_elements(By.CLASS_NAME, "prevnextbutton")
                for next_page in next_pages:
                    if next_page.get_attribute('title') == 'Next page':
                        next_page_link = next_page.get_attribute('href')
                        if next_page_link and next_page_link not in self.brand_page_links:
                            self.brand_page_links.append(next_page_link)
                            self._fetch_phone_links(driver)

            except Exception as e:
                print(f"Error fetching next page for brand {brand}")
        driver.quit()

    def _fetch_phone_links(self, driver) -> None:
        """
        Fetch phone links from the brand page.
        """
        try:
            makers_div = driver.find_element(By.CLASS_NAME, "makers")
            phones = makers_div.find_elements(By.TAG_NAME, "a")
            for phone in phones:
                self.phone_page_links.append(phone.get_attribute('href'))
        except Exception as e:
            print(f"Error fetching phone links")
            
    def _get_phone_page_links(self) -> list:
        
        if len(self.phone_page_links) == 0:
            my_file = open(f"{os.getcwd()}/../results/phone_links_to_scrap.txt", "r")
            page_links = sorted(set(my_file.read().split("\n")))
        else:
            page_links = self.phone_page_links
            
        return page_links[1:]
    
    def _get_phone_df(self) -> pd.DataFrame:
        if os.path.isfile(f'{os.getcwd()}/../results/terminales.csv'):
            phone_df = pd.read_csv(f'{os.getcwd()}/../results/terminales.csv')
        else:
            phone_df = pd.DataFrame(columns=['MODEL_NAME', 'RELEASE_DATE', 'ANNOUNCE_DATE', 'OS', 'MODEL_VERSION', 'NFC', 'PRICE'])
        
        return phone_df

    def _extract_element_text(self, driver, selector) -> str:
        """
        Function to obtain the text of an element, returning None if not found.
        """
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            return element.text
        except NoSuchElementException:
            return None

    def scrape_brand_links(self) -> None:
        """
        Fetch the initial list of brand links from the main page.
        """
        print("---------- Starting the process of obtaining phone links ----------\n")

        driver = webdriver.Chrome(options=self.options)
        try:
            driver.get('https://www.gsmarena.com/makers.php3')
            st_text_div = driver.find_element(By.CLASS_NAME, "st-text")
            links = st_text_div.find_elements(By.TAG_NAME, "a")
            self.brand_page_links = [link.get_attribute('href') for link in links]
            driver.quit()
        except Exception as e:
            print(f"Error fetching brand links")
            driver.quit()

        self._fetch_brand_phone_links()
        self.phone_page_links = sorted(self.phone_page_links)
        
        with open(f"{os.getcwd()}/../results/phone_links_to_scrap.txt", "w") as output:
            for link in self.phone_page_links:
                output.write(f'{link}\n')
        
        with open(f"{os.getcwd()}/../results/phone_links_scrapped.txt", 'w') as file:
            pass 

        
    def scrape_phone_features(self) -> None:
        """
        Fetch the features of each phone by visiting its respective link.
        """
        print("---------- Starting the process of obtaining phone features ----------\n")

        driver = webdriver.Chrome(options=self.options)

        page_links = self._get_phone_page_links()
        page_links_to_scrap = page_links[:]
            
        my_file = open(f"{os.getcwd()}/../results/phone_links_scrapped.txt", "r")
        page_links_scrapped = sorted(set(my_file.read().split("\n")))[1:]
            
        for link in page_links_to_scrap:
            if link not in page_links_scrapped:
                try:
                    time.sleep(random.uniform(1, 3))  # Random wait to mimic human behavior
                    driver.get(link)

                    # Data extraction
                    model_name = self._extract_element_text(driver, 'h1[data-spec="modelname"]')
                    release_date = self._extract_element_text(driver, 'span[data-spec="released-hl"]')
                    announce_date = self._extract_element_text(driver, 'td[data-spec="year"]')
                    operating_system = self._extract_element_text(driver, 'td[data-spec="os"]')
                    model_version = self._extract_element_text(driver, 'td[data-spec="models"]')
                    nfc = self._extract_element_text(driver, 'td[data-spec="nfc"]')
                    price = self._extract_element_text(driver, 'td[data-spec="price"]')

                    # Add data to the list
                    phone_data = [[model_name, release_date, announce_date, operating_system, model_version, nfc, price]]
                    df = pd.DataFrame(phone_data,columns=['MODEL_NAME', 'RELEASE_DATE', 'ANNOUNCE_DATE', 'OS', 'MODEL_VERSION', 'NFC', 'PRICE'])
                    self.phone_df = pd.concat([self.phone_df,df])
                    
                    self.phone_df.to_csv(f'{os.getcwd()}/../results/terminales.csv', index = False)
                    
                    page_links_scrapped.append(link)
                    
                    with open(f"{os.getcwd()}/../results/phone_links_scrapped.txt", "w") as output:
                        for element in page_links_scrapped:
                            output.write(f'{element}\n')
                        
                    page_links.remove(link)
                    
                    with open(f"{os.getcwd()}/../results/phone_links_to_scrap.txt", "w") as output:
                        for element in page_links:
                            output.write(f'{element}\n')
                    
                    print(f'Scraped the following link: {link}')

                except Exception as e:
                    print(f"Error processing link {link}: {e}")

        driver.quit()
