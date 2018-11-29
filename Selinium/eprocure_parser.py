#!/usr/bin/python

import requests
from bs4 import BeautifulSoup

from bs4 import BeautifulSoup
from selenium import webdriver


ACTIVE_TENDER_COUNT_KEY = "tend_cl2"
ACTIVE_TENDER_KEY = "Active Tenders" 

parsed_result = {}

dynamic = webdriver.Firefox()
dynamic.get('https://eprocure.gov.in/cppp/')
#TODO: Handle the improper empty loading of buffer as dynamic.get keeps waiting for the response buffer.
# This can be handled with looped retries with timeout criteria.
dynamic_page = dynamic.page_source
dynamic.close()

print "Page successfully got closed."
#    FOR STATIC PAGES #
#static_page = requests.read("https://eprocure.gov.in/cppp/")
# Create a BeautifulSoup object
#soup = BeautifulSoup(page.text, 'html.parser')
#

# FOR DYNAMIC PAGES #
soup = BeautifulSoup(dynamic_page, 'html.parser')
#

# Pull all text from the BodyText div
artist_name_list = soup.find(class_='boxc2')

# Pull text from all instances of <a> tag within BodyText div
artist_name_list_items = artist_name_list.find('a').find_all('div')

# Create for loop to print out all div tag content within boxc2 class attribute.
for artist_name in artist_name_list_items:
    value = artist_name.get('class')
    if value is not None:
        if value[0] == ACTIVE_TENDER_COUNT_KEY:
            results = artist_name.contents[0]
parsed_result.update({ACTIVE_TENDER_KEY : results})
#print(artist_name.prettify())

print "============ TENDER STATISTICS ============"
for key in parsed_result:
    print "\t %s : %s" % (key, parsed_result[key])
