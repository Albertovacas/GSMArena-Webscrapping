from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from threading import Thread, Semaphore

class WebScraper:
    """
    Class to perform web scraping on a given website to extract brand and phone links.
    """

    def __init__(self, options) -> None:
        """
        Initialize the WebScraper with the provided WebDriver options.
        """

        self.options = options
        self.brand_links = []
        self.phone_links = []
        self.data = []

    def _get_phones_and_next_page_brand(self) -> None:
        """
        Recursively fetch links from the next pages for each brand.
        """
        driver = webdriver.Chrome(options=self.options)
        for brand in self.brand_links:
            print(brand)
            time.sleep(0.3)
            try:
                driver.get(brand)
                next_pages = driver.find_elements(By.CLASS_NAME, "prevnextbutton")
                for next_page in next_pages:
                    if next_page.get_attribute('title') == 'Next page':
                        next_page_link = next_page.get_attribute('href')
                        if next_page_link and next_page_link not in self.brand_links:
                            self.brand_links.append(next_page_link)
                            self._get_phone_links(driver)

            except Exception as e:
                print(f"Error fetching next page for brand {brand}")
        driver.quit()

    def _get_phone_links(self, driver) -> None:
        """
        Fetch phone links from the brand page.
        """

        try:
            makers_div = driver.find_element(By.CLASS_NAME, "makers")
            phones = makers_div.find_elements(By.TAG_NAME, "a")
            for phone in phones:
                self.phone_links.append(phone.get_attribute('href'))
        except Exception as e:
            print(f"Error fetching phone links")

    def _get_element_text(self, driver, selector) -> None:
        """
        Función para obtener el texto de un elemento, devolviendo None si no se encuentra.
        """

        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            return element.text
        except:
            return None

    def _get_features(self,semaphore,link, driver):

        semaphore.acquire()

        try:
            time.sleep(0.3)
            driver.get(link)

            # Extracción de datos
            model_name = self._get_element_text(driver, 'h1[data-spec="modelname"]')
            release_date = self._get_element_text(driver, 'span[data-spec="released-hl"]')
            announce_date = self._get_element_text(driver, 'td[data-spec="year"]')
            os = self._get_element_text(driver, 'td[data-spec="os"]')
            model_version = self._get_element_text(driver, 'td[data-spec="models"]')
            nfc = self._get_element_text(driver, 'td[data-spec="nfc"]')
            price = self._get_element_text(driver, 'td[data-spec="price"]')

            print(f'Se ha scrapeado el siguiente enlace: {link}')

            # Añadir los datos a la lista
            self.data.append([model_name, release_date, announce_date, os, model_version, nfc, price])

        except Exception as e:
            print(f"Error al procesar el enlace {link} : {e}")

        semaphore.release()

    def get_links(self) -> None:
        """
        Fetch the initial list of brand links from the main page.
        """

        print("---------- Comienza el proceso de obtencion de enlances de los terminales ----------\n")

        driver = webdriver.Chrome(options=self.options)

        try:
            driver.get('https://www.gsmarena.com/makers.php3')
            st_text_div = driver.find_element(By.CLASS_NAME, "st-text")
            links = st_text_div.find_elements(By.TAG_NAME, "a")
            self.brand_links = [link.get_attribute('href') for link in links]
            driver.quit()
        except Exception as e:
            print(f"Error fetching brand links")
            driver.quit()

        self._get_phones_and_next_page_brand()
        self.phone_links = sorted(self.phone_links)

    def scrap_features(self) -> pd.DataFrame:

        print("\n---------- Comienza el proceso de obtencion de caracteristicas de los terminales ----------\n")

        data = []
        driver = webdriver.Chrome(options=self.options)

        threads = list()
        semaphore = Semaphore(4)

        for link in self.phone_links:
            t = Thread(target = self._get_features, args=(semaphore, link, driver))
            threads.append(t)
            t.start()
            time.sleep(1)

        # wait for the threads to complete
        for t in threads:
            t.join()

        driver.quit()
        return pd.DataFrame(data,columns = ['MODEL_NAME','REALEASE_DATE','ANNOUNCE_DATE','OS','MODEL_VERSION','NFC','PRICE'])