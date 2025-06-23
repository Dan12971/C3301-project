
import requests
from bs4 import BeautifulSoup 
import pymongo 
import lxml.etree as ET
                                               

def get_soup(url):                                  
	response = requests.get(url)
	html = BeautifulSoup(response.content, "lxml")                                                  
return html
                                                
def scrape_data(url, request_method, crawling_period, headers, db_name, scraping_class):           
	scraping_class.db = pymongo.MongoClient("mongodb://localhost:27017").db                     
    # Connect to the MongoDB database               scraping_class.db["data"] = pymongo.database.Database(scrapping_class.db["db"])
                                                    # Set the collection name to be used for data storage                                           scraping_class.db["data"].collection_name = "scraped_data"                                  
    # Set the required parameters for the website (URL, Request Method, Crawling Period, Headers, Scraper Class, and Database Connection)
request_params = {                                  "url": url,                                     "request_method": request_method,
        "crawling_period": crawling_period,             "headers": headers,
        "scraper_class": scraping_class             }
                                                    # Scrape the data                               soup = get_soup(url)
html_content = scraper.get_html(soup)                                                           # Store the data in the MongoDB database
scraping_class.db["data"].insert_one({              "_id": scraping_class.db["data"].last_insert_id(),
        "url": url,                                     "request_method": request_method,               "crawling_period": crawling_period,
        "headers": headers,                             "html": html_content                        })
def get_html(url):                                  response = requests.get(url)
return response.content                                                                     
def get_soup(url):
	soup = BeautifulSoup(get_html(url), "lxml")     
return soup                                 
if __name__ == "__main__":                          
    url = "https://www.example.com"
    request_method = "GET"
    crawling_period = "3 days"
    headers = {"User-Agent": "Mozilla/5.0 (X11; UUID\uD83C\uDC4E)"}
    scraping_class = {
        "db": "data",                                   "scraper_class": Scraper
    }                                           
    scraping_object = Scraper(url, request_method, crawling_period, headers, scraping_class)
    scraper = scraping_object.scrape_data()         scraping_object.get_soup(url)
    scraping_object.get_html(url)               ```
