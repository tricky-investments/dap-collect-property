from bs4 import BeautifulSoup
import json
import requests

import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.http.request.form import FormRequest
from scrapy.loader import ItemLoader

from lib.abstract import Api, Crawler


class RealtyInUsAPI(Api):
    API_NAME = "Realty in US Api (Realtor) from RapidApi"

    def _call_endpoint(self, method, endpoint, params):
        url = 'https://' + self.api_config['x-rapidapi-host'] + endpoint
        headers = self.api_config

        response = requests.request(method, url, headers=headers, params=params)
        return response.status_code, json.loads(response.text)

    def list_for_sale(self, params):
        if not all(elem in params.keys() for elem in ['city', 'state_code', 'offset', 'limit']):
            return False, 'Some required fields are missing.'

        return self._call_endpoint('GET', '/properties/v2/list-for-sale', params)

    def property_detail(self, params):
        if 'property_id' not in params.keys():
            return False, 'property_id is required.'

        return self._call_endpoint('GET', '/properties/v2/detail', params)


class UsRealEstateAPI(Api):
    API_NAME = "US Real Estate Api from RapidApi"

    def _call_endpoint(self, method, endpoint, params):
        url = 'https://' + self.api_config['x-rapidapi-host'] + endpoint
        headers = self.api_config

        response = requests.request(method, url, headers=headers, params=params)
        return response.status_code, json.loads(response.text)

    def get_average_rates(self, params):
        if 'postal_code' not in params.keys() or params['postal_code'] is None:
            return False, 'postal_code is required'

        return self._call_endpoint('GET', '/finance/average-rate', params)


class MortgageCalculatorCrawler(Crawler):

    def initiate_params(self, params):
        self.params = params

    def run(self):

        response = requests.request('POST', self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        key = soup.find('input', {'name': 'mortgage-calculator-plus'}).get('value')

        form_data = {
            'param[action]': 'calculate',
            'mortgage_calculator_plus': key,
            'cal': 'Calculate'
        }

        for key in self.params.keys():
            form_data.update({f'param[{key}]': self.params[key]})

        response = requests.request('POST', url=self.url, data=form_data)
        soup = BeautifulSoup(response.text, 'html.parser')
        summary = soup.find('div', {'class': 'repayment-block'})
        payment = list(summary.find_all('div', {'class': 'left-cell'})[0].children)[1].get_text()

        for i in payment:
            if i in ['$', ',']:
                payment = payment.replace(i, '')

        return float(payment)


if __name__ == '__main__':
    parameters = {
        'homevalue': '549000',
        'downpayment': '50000',
        'downpayment_type': 'money',
        'interest_rate': '2.763',
        'term': '30',
        'start_month': '09',
        'start_year': '2021',
        'property_tax': '10980.0',
        'pmi': '0.6',
        'hoi': '1413.67',
        'hoa': '0',
        'milserve': '2',
        'refiorbuy': '1',
        'credit_rating': '0',
        'draw_charts': '1',
        'principal': '499000'
    }

    crawler = MortgageCalculatorCrawler(url='https://www.mortgagecalculator.org')
    crawler.initiate_params(params=parameters)
    crawler.run()
