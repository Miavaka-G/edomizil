from datetime import datetime, timedelta
from random import randint, uniform
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import json
import os
import sys
import time
import csv

import undetected_chromedriver as uc #15 10 2026

load_dotenv()




class EdomizilScraper(object):

    def __init__(self,filename:str, dest_name:str, date_start:str, date_end:str) -> None:
        
        self.data = []
        self.filename = filename
        self.dest_name = dest_name
        self.date_start = datetime.strptime(date_start, '%d/%m/%Y').strftime('%Y-%m-%d')
        self.date_end = datetime.strptime(date_end, '%d/%m/%Y').strftime('%Y-%m-%d')
        self.week_scrap = datetime.strptime(date_start, "%d/%m/%Y").strftime("%d_%m_%Y")
        self.cycle_count = 0
        self.max_cycle = 30

        self.base_log = os.environ.get("LOG_FOLDER_PATH")
        self.base_static = os.environ.get('STATIC_FOLDER_PATH')
        self.base_output = os.environ.get("OUTPUT_FOLDER_PATH")
        self.base_config = os.environ.get("CONFIG_FOLDER_PATH")
        self.base_dests = os.environ.get("DESTS_FOLDER_PATH")

        # self.chrome_options = webdriver.ChromeOptions()
        # self.chrome_options.add_argument('--disable-gpu')
        # self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # self.chrome_options.add_argument('--disable-search-engine-choice-screen')
        # # self.chrome_options.add_argument('--incognito') #15 10 2026
        # self.chrome_options.add_extension(f"{os.environ.get('EXTENSION_PATH')}")
        # #Argument à utiliser surtout en multi instance pour éviter des crash de chrome 13 07 2026
        # self.chrome_options.add_argument("--disable-dev-shm-usage")
        # #ajout 28 07 2026
        # # self.chrome_options.add_argument('--disable-infobars')
        # # self.chrome_options.add_argument('--no-sandbox')
        # # self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        # self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # self.chrome_options.add_experimental_option('useAutomationExtension', False)
        # #fin 21 07 2026
        # # self.chrome_options.add_argument('--headless')
        # #24 09 2026 : alléger sans image
        # # self.chrome_options.add_argument('--blink-settings=imagesEnabled=false') un vrai navigateur charge les images (risque cloudfare si utilsé)
        # self.chrome_options.add_argument('--disk-cache-size=1')
        # self.chrome_options.add_argument('--media-cache-size=1')

        # self.firefox_options = webdriver.FirefoxOptions()
        # self.firefox_options.add_argument('--disable-gpu')
        # # self.firefox_options.add_argument('--incognito')
        # # self.chrome_options.add_argument('--headless')

        # self.use_new_driver() mis dans le go to

    def options_chrome(self,):
        chrome_options = webdriver.ChromeOptions() 
        # chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-search-engine-choice-screen')
        # self.chrome_options.add_argument('--incognito') #15 10 2026
        # chrome_options.add_extension(f"{os.environ.get('EXTENSION_PATH')}")
        #Argument à utiliser surtout en multi instance pour éviter des crash de chrome 13 07 2026
        chrome_options.add_argument("--disable-dev-shm-usage")
        #ajout 28 07 2026
        # self.chrome_options.add_argument('--disable-infobars')
        # self.chrome_options.add_argument('--no-sandbox')
        # self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        chrome_options.add_experimental_option('useAutomationExtension', False) 
        #fin 21 07 2026
        # self.chrome_options.add_argument('--headless')
        #24 09 2026 : alléger sans image
        # self.chrome_options.add_argument('--blink-settings=imagesEnabled=false') un vrai navigateur charge les images (risque cloudfare si utilsé)
        chrome_options.add_argument('--disk-cache-size=1')
        chrome_options.add_argument('--media-cache-size=1')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.binary_location="/usr/bin/google-chrome" #dans le .18 il y a deux chrome, un 144 et un chromium 153 , on utilise le 144

        self.firefox_options = webdriver.FirefoxOptions()
        self.firefox_options.add_argument('--disable-gpu')
        # self.firefox_options.add_argument('--incognito')
        # self.chrome_options.add_argument('--headless')
        return chrome_options

    def normalize_url(self, url:str, date:str) -> str:
        url_params = list(parse_qs(urlparse(url).query).keys())
        if 'c' in url_params and 'hl' in url_params:
            return url 
        else:
            if 'c' not in url_params:
                url += '&c=EUR'
            if 'hl' not in url_params:
                url += '&hl=fr_CH'
            return url + f"&arrival={date}"

    def get_file_content(self, filepath:str) -> object:
        with open(filepath, 'r') as openfile:
            return json.loads(openfile.read())
        
    def create_files(self) -> None:
        print("  ==> creating logs")
        default_log = {'last_dest': 0}

        self.logfile_path = f"{self.base_log}/edomizil/{self.week_scrap}/start/{self.filename}.json"
        self.dest_path = f"{self.base_dests}/{self.dest_name}.json"
        self.output_path = f"{self.base_output}/edomizil/{self.week_scrap}/results/{self.filename}.csv"

        if not Path(self.output_path).exists():
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            pd.DataFrame(columns=[
                'date_scrap',
                'date_debut',
                'date_fin',
                'price',
                'identifiant',
                'typologie',
                'nom'
            ]).to_csv(self.output_path, index=False)

        if not Path(self.logfile_path).exists():
            os.makedirs(os.path.dirname(self.logfile_path), exist_ok=True)
            with open(self.logfile_path, 'w') as openfile:
                openfile.write(json.dumps(default_log, indent=4))
            
        if not Path(self.dest_path).exists():
            print('destination files not found')
            sys.exit()
            
        
    def load_configs(self) -> None:
        print(' ==> load config files')
        self.history = self.get_file_content(self.logfile_path)
        print(f'history = {self.history}')
        self.destinations = self.get_file_content(self.dest_path)
        print(f'{len(self.destinations)} destinations loaded')

    def set_history(self, key:str, value:object) -> None:
        self.history[key] = value
        with open(self.logfile_path, 'w') as openfile:
            openfile.write(json.dumps(self.history, indent=4))

    # def use_new_driver(self) -> None: #before 24 09 2026
    #     try:
    #         self.driver.quit()
    #         self.driver = webdriver.Chrome(options=self.chrome_options)
    #     except Exception:
    #         self.driver = webdriver.Chrome(options=self.chrome_options)
    #         # self.driver = webdriver.Firefox(options=self.firefox_options)
        
    #     # self.driver.maximize_window() #commenté le 28 07 2026 pour alléger le serveur
    #     self.driver.set_window_size(1920, 1080)

    def use_new_driver(self) -> None: #24 09 2026
        print("   ==> Tentative de fermeture de l'ancien driver...")
        try:
            self.driver.quit()
        except Exception as e:
            print(f"   ==> Impossible de fermer proprement le driver (efa maty) : {e}")

        time.sleep(1)

        print("   ==> Initialisation de la nouvelle fenêtre Chrome...")
        try:
            self.driver = webdriver.Chrome(options=self.options_chrome())
            # self.driver = uc.Chrome(options=self.options_chrome(), version_main=144) #144 version chrome du .18
        except Exception as e:
            print(f"   ==> Échec initial du lancement de Chrome ({e}). Nouvelle tentative dans 15 secondes...")
            time.sleep(1) 
            self.driver = webdriver.Chrome(options=self.options_chrome())
            # self.driver = uc.Chrome(options=self.options_chrome(), version_main=144, browser_executable_path="/usr/bin/google-chrome")
        
        # Configuration de la taille de la fenêtre (votre code)
        try:
            self.driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"   ==> set_window_size ignoré : {e}")
        self.driver.set_page_load_timeout(30)

    def goto_page(self, url:str, date:str) -> str:
        if self.cycle_count >= self.max_cycle:
            print('     ')
            print(f'   ==> Meme driver utilisé {self.cycle_count} / {self.max_cycle} , CHANGEMENT DE DRIVER')
            print('     ')
            self.use_new_driver()
            self.cycle_count = 0
        elif self.cycle_count < self.max_cycle:
            print('     ')
            print(f'   ==> Meme driver utilisé {self.cycle_count} / {self.max_cycle} ')
            print('     ')
        try:
            normalized_url = self.normalize_url(url, date)
            print(f"    => {normalized_url}")
            test_url = "https://www.e-domizil.ch/rental/c2b595ce31e3499a1d576fdce31290ed?location=5460aeabb3b30&pricetype=totalPrice&duration=7&timestamp=2025-02-10T09%3A52%3A13%2B01%3A00&id=c2b595ce31e3499a1d576fdce31290ed&searchId=1adbef2678a920c0&screen=search&isHotel=0&clickId=VY6G7DWP4N0L7X3S&sT=dateless&prodName=JM&prodSource=Search&c=EUR&hl=fr_CH&arrival=2025-02-22"
            self.driver.get(normalized_url)
            #check if the link is unavailable 21 02 2025
            time.sleep(uniform(0.5,1.2)) #changement 05 08 2026
            try:
                if self.driver.find_element(By.XPATH,'//*[text()="404 Seite nicht gefunden"]'):
                    print("                     ")
                    print("erreur 404, quit the function for the next url")
                    print("                     ")
                    return "next url"
            except:
                pass
            # WebDriverWait(self.driver, 3).until(EC.element_to_be_selected((By.XPATH,'//*[@id="jager-app"]/div/div[5]/div/div[2]/div[2]/button[2]/span/span/span')))
            # self.driver.find_element(By.XPATH,'//*[@id="jager-app"]/div/div[5]/div/div[2]/div[2]/button[2]/span/span/span').click()

            #28 07 2026 Pour le cloufire vérification humaine
            # if self.driver.find_elements(By.ID, 'ACsu8'): ça a changé
            if self.driver.find_elements(By.ID, 'oqnd2'): #MAJ selecteur detection human 16 08 2026
                print("         ")
                print("COUDFARE VERIFICATION HUMAINE, new driver")
                self.use_new_driver()
                time.sleep(uniform(2.1, 4.2)) 
                return self.goto_page(url, date)
                # WebDriverWait(self.driver, 300).until(EC.visibility_of_element_located((By.XPATH, "//div[@data-test='rental-sidebar']")))

            #06 08 2026 Page error, url établissement vraiment en 404
            if self.driver.find_elements(By.ID, 'page-error'):
                print("         ")
                print("PAGE ETABLISSEMENT ERROR 404 , next url")
                return "next url"

            WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@data-test='rental-sidebar']")))
            
            waiting_count = 0
            #28 07 2026 : vérifier la présence du rental sidebar n'est pas très correcte car la edomizil peut soudainement se recharger , on va mettre une boucle sur True et breaker si ok , continuer la recherche du sidebar si pas trouvé (on est là déja passer par le webdriver wait)
            while True:
            # while "disponibilité en cours de vérification" in self.driver.find_element(By.XPATH, "//div[@data-test='rental-sidebar']").text.lower().strip():
                try:
                    content_disponibility = self.driver.find_element(By.XPATH, "//div[@data-test='rental-sidebar']").text.lower().strip()
                    if "disponibilité en cours de vérification" in content_disponibility:
                        print('   =>  waiting for data to be loaded')
                    else:
                        break #car le contenu est chargé et on peut continuer
                #ajouté le 28 07 2026
                except (StaleElementReferenceException, NoSuchElementException):
                    print('   =>  Rafraichissement du DOM détecté, recheck')
                    time.sleep(0.5)
                    continue
                # print("    =>  waiting for data to be loaded")
                if waiting_count >= 20:
                    #MAJ temps d'attente disponibilité de l'offre car 5 secondes ne suffit pas sur serveur , 12 01 2026
                    waiting_count = 0
                    # input('check')
                    self.use_new_driver()
                    time.sleep(uniform(1.5,4.5))
                    # self.goto_page(url, date)
                    #28 07 2026 mieux vaut stopper la fonction pour passer à une autre
                    return self.goto_page(url, date)
                time.sleep(1)
                waiting_count += 1
        except TimeoutException:
            print('     ===> TimeoutException')
            #21 07 2026 : parfois ça passe la vérification humaine, on va ajouter un delai très aléatoire
            time.sleep((uniform(0.5,1.5)))
            #fin 21 07 2026
            self.use_new_driver()
            #28 07 2026 : toujours stopper la fonction en cours pour reapeeler
            return self.goto_page(url, date)
            # self.goto_page(url, date)

        #24 09 2026 : gérer les crash en simultané à cause de la roation de ip programme ip manager de maeva (je pense)
        except WebDriverException as e:
            error_msg = str(e).lower()
            if "tab crashed" in error_msg or "session deleted" in error_msg or "invalid session id" in error_msg:
                print("                     ")
                print("[ALERTE VPN] Onglet planté / Session perdue. Réinitialisation...")
                print("                     ")
                # Optionnel : ajouter une pause de 15s si le VPN met du temps à se reconnecter
                time.sleep(15) 
                self.use_new_driver()
                return self.goto_page(url, date)
            else:
                # Si c'est une autre erreur WebDriver non liée au crash de l'onglet, on la relance
                raise e
        self.cycle_count += 1

    #effacer cache en cours d'exécution
    def clear_cache(self,) -> None:
        try:
            self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
            print("Le cache de Chrome a été vidé avec succès.")
        except Exception as e:
            print(f"Erreur lors de la tentative de vidage du cache : {e}")
            pass
        time.sleep(uniform(0.5, 0.9))  # Pause aléatoire pour simuler un comportement humain
        

    def soupify(self, element:str) -> object:
        return BeautifulSoup(element, 'lxml')

    def page_info_is_valid(self) -> bool:
        #24 09 2026 : parfois il y a une erreur dedans , on check
        print('             ')
        print('    =>  verifying page , 3 tentation de vérification sinon voir si le site a changé de structure')
        trying_max = 3
        for trying in range(trying_max):
            try:
                info_container = self.driver.find_element(By.XPATH, "//div[@data-test='rental-sidebar']").get_attribute('innerHTML')
                info_cleaned = self.soupify(info_container)
                info_displayed = info_cleaned.find('div', {'data-test':"available-badge"}) and 'bg-success-super-light' in info_cleaned.find('div', {'data-test':"available-badge"})['class']
                if info_displayed: 
                    print('    =>  data displayed and available')
                else:
                    print('    =>  data not displayed or not available')
                return info_displayed
            except StaleElementReferenceException as e: #c'est l'erreur capturé en console parfois
                if trying == trying_max -1:
                    print('             ')
                    input(f"L'erreur persiste donc plus un probleme de chargement mais la page a changé peut etre, VERIFIER DANS LE NAVIGATEUR)")
                print('             ')
                print(' -- La page a peut etre besoin de quelques seconde de chargement --- ')
                time.sleep(1)

    def extract_data(self) -> None:
        print('    =>  extracting data')
        time.sleep(3)
        soupe = self.soupify(self.driver.page_source)
        info_container = soupe.find("div", {"data-test":'rental-sidebar'})
        identifiant = ""
        typologie = ""
        try:
            identifiant = info_container.find('div', {'class':"bdtlrsm bdtrrsm bgc-gray-extra-light c-gray-dark pv4 tac text-small"}).find_all('span')[-1].text.strip()
        except:
            try:
                print('----- Second selector of identifiant')
                identifiant = soupe.find("div", "c-gray-extra-dark fwb").text.strip()
            except:
                try:
                    print('------ Third selector of identifiant') #07 10 2026
                    identifiant = soupe.find("div", {'class' : 'c-gray-extra-dark font-bold'}).text.strip()
                except:
                    input('identifiant not found, check selector in navigator')
        try:
            typologie = info_container.find('div', {'class':"text-overflow text-small txt-strong"}).text.strip()
        except:
            print('----- 2eme nouvelle affichage for typology')
            try:
                typologie = soupe.find('span', {'class':"text-medium fwb db cols>m4"}).text.strip()
            except:
                try:
                    #MAJ 06 11 2025
                    print('----- 3eme nouvelle affichage for typology')
                    typologie = soupe.find('span', {'class':"db cols>m4 text-medium fwb"}).text.strip()
                except:
                    try:
                        #MAJ 06 11 2025
                        print('----- 4eme nouvelle affichage selector for typology')
                        typologie = soupe.find('span', {'class':"db cols>m4 text-large"}).text.strip()
                    except:
                        #MAJ 07 10 2026
                        try:
                            print('----- 5eme nouvelle affichage selector for typology')
                            typologie = soupe.find('span', {'class':"block cols>m4 text-large"}).text.strip()
                        except:
                            input('typology not found, check selector in navigator')
        # input('pause')
        #selecteur ancien affichage de nom:
        try:
            nom = soupe.find('div', {'data-test':"rental-sidebar"}).find_all('div', {'class':'text-overflow'})[1].text.strip().replace(',', ' -')
            print("anienne affichage")
            # input("pause")
        except:
            try:
               #avant 31 07 2025 nom = soupe.find('article', {'class':"df db-print"}).find('span', {'class':'c-gray-dark text-medium'}).text.strip().replace(',', ' -')
                #MJ 06 11 2025
                nom = soupe.find('span', {'class':'text-medium c-gray-dark'}).text.strip().replace(',', ' -')
                print("nouvelle afichage")
                # nom = soupe.find('article', {'class':"df db-print"}).find('h1', {'role':'button'}).text.strip().replace(',', ' -')
            except:
                try:
                    #MAJ 06 11 2025
                    print('second nom nouvel affichage (TYPOLOGIE AFFICHé PAS EN GRAS)')
                    nom = soupe.find_all('span', {'class':'text-large'})[1].text.strip().replace(',', ' -') #le 1er est le vrai
                    if "Appartement" in nom or "Appartements" in nom:
                        input(f'FAUSSé -> {nom}, check selector in navigator')
                except:
                    print("pas de bon selecteur nom")
                    input("check naviguator")
                # nom = soupe.find('article', {'class':"df db-print"}).find('h1', {'class':'subheading-medium mv0'}).text.strip().replace(',', ' -')
        # input("price")
        #MAJ 07 10 2026 + nouveau formattage
        try:
            price = info_container.find('div', {'data-test':"total-price"}).find('span', {'class':'wsnw'}).text.replace('\u202f', '').replace('\xa0','').replace(' ', '')
        except:
            try:
                print('---- second selector for price')
                price = info_container.find('div', {'data-test':"total-price"}).find('span', {'class':'whitespace-nowrap'}).text.replace('\u202f', '').replace('\xa0','').replace(' ', '')
            except:
                # try:
                #     print('----- third selector for price')
                #     price = info_container.find('div', {'data-test':"total-price"}).find('span', {'class':'text-large'}).text.replace('\u202f', '').replace(' ', '')
                # except:
                input('price not found, check selector in navigator')

        if price[0] == "€":
            price = price.replace('€', '').replace(',', '')
        else:
            price = price.replace('€', '').replace('.', '').replace(',', '.')
        arrival_date = datetime.strptime(parse_qs(urlparse(self.driver.current_url).query)['arrival'][0], "%Y-%m-%d").strftime("%d/%m/%Y")
        data = {
            'date_scrap': datetime.now().strftime("%d/%m/%Y"),
            'date_debut': arrival_date,
            'date_fin': (datetime.strptime(arrival_date, "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y"),
            'price': price,
            'identifiant': identifiant,
            'typologie': typologie,
            'nom': nom
        }

        print(data)
        self.data.append(data)

        self.clear_cache()

    def save_data(self) -> None:
        print('    =>  saving data')
        field_names = [
            'date_scrap',
            'date_debut',
            'date_fin',
            'price',
            'identifiant',
            'typologie',
            'nom'
        ]
        with open(self.output_path, 'a', newline='', encoding='utf-8') as f_object:
            dictwriter_object = csv.DictWriter(f_object, fieldnames=field_names)
            dictwriter_object.writerows(self.data)
        self.data.clear()

    def start(self) -> None:
        self.create_files()
        self.load_configs()
        self.use_new_driver()
        for k in range(self.history['last_dest'], len(self.destinations)):
            print(f" ==> {k + 1} / {len(self.destinations)} destinations")
            dates = pd.bdate_range(
                                    start=self.date_start, 
                                    end=self.date_end, 
                                    freq='C', 
                                    weekmask='Sat'
                                ).strftime('%Y-%m-%d').to_list()
            for j in range(len(dates)):
                print(f'    => week {j + 1} / {len(dates)} : {datetime.strptime(dates[j], "%Y-%m-%d").strftime("%d-%m-%Y")} => {(datetime.strptime(dates[j], "%Y-%m-%d") + timedelta(days=7)).strftime("%d-%m-%Y")}')
                continue_or_break = self.goto_page(self.destinations[k], dates[j])
                #break this boucle for next_url 21 02 2025
                if continue_or_break == "next url":
                    # input(f"{continue_or_break}")
                    print("         ")
                    print("next url now")
                    print("         ")
                    time.sleep(uniform(3.1, 5.2)) #ajouté 12 10 2026 par demande de Nicolas mettre encore un peu plus de temps
                    break
                if self.page_info_is_valid():
                    self.extract_data()
                    self.save_data()
                print('---- sleeping quelques seconds before next week ---- ')
                time.sleep(uniform(1.9, 2.6)) #24 09 2026
                new_index = k + 1 
                self.set_history('last_dest', new_index)
        print('scrap finished !')
