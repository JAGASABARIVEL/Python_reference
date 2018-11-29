from time import sleep
import requests
from lxml import html
import json

STOCK_PRICE = {}

def html_fetch(page, idno):
    while True:
        sleep(3)
        try:
            doc = html.fromstring(page.content)
            XPATH_SALE_PRICE = '//span[contains(@id, \"%s\")]/text()'% (idno)

            RAW_SALE_PRICE = doc.xpath(XPATH_SALE_PRICE)

            SALE_PRICE = ' '.join(''.join(RAW_SALE_PRICE).split()).strip() if RAW_SALE_PRICE else None

            if page.status_code!=200:
                raise ValueError('captha')
            data = {
                    'SALE_PRICE':SALE_PRICE
                    }

            return data
        except:
            pass

def fetchstockquotes():
    global STOCK_PRICE
    STOCKS = {
    'nse' : 'ref_717329_l',
    'reliance' : 'ref_4674509_l'
    }
    for stock in STOCKS:
    # ref_717329_l
        base_url = 'https://finance.google.com/finance?q='
        request = requests.session()
        content = request.get(base_url + stock, verify=False)
        price = html_fetch(content, idno=STOCKS[stock])['SALE_PRICE']
        STOCK_PRICE.update({stock : { "Stock Price" : price } })

fetchstockquotes()
print "Stock Detail : ", json.dumps(STOCK_PRICE, indent=2)
