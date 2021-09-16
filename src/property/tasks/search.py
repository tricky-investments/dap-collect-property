import datetime
from abc import ABC

from .helpers import calculator, externals

from lib.abstract import Task


class SearchPropertiesTask(Task):
    TASK_NAME = "Property Search Task"

    def __str__(self):
        return self.TASK_NAME

    def load_settings(self, settings):
        self.realty_in_us_config = settings['realty_in_us_config']
        self.us_real_estate_config = settings['us_real_estate_config']
        self.mortgage_calc_url = settings['mortgage_calc_url']
        self.last_run = datetime.datetime.fromisoformat(settings['last_run'])

    def load_parameters(self, params):

        self.realty_in_us_params = {}
        keys = ['city', 'state_code', 'limit', 'offset', 'prop_type', 'features', 'price_min', 'price_max']
        for key in keys:
            if key in params.keys():
                self.realty_in_us_params.update({key: params[key]})

        self.us_real_estate_params = {}
        keys = ['postal_code']
        for key in keys:
            if key in params.keys():
                self.us_real_estate_params.update({key: params[key]})

        # MORTGAGE PARAMS HERE
        self.mortgage_params = {}
        keys = ['downpayment', 'downpayment_type', 'pmi', 'loan_type', 'refi']
        for key in params.keys():
            if key in params.keys():
                self.mortgage_params.update({key: params[key]})

    def run(self):

        success = True
        data = {}

        """
        COLLECT PROPERTIES

        Use Realty in US API to collect properties from Realtor.com
        """
        now = datetime.datetime.now()

        if not all(i in self.realty_in_us_params.keys() for i in ['city', 'state_code', 'offset', 'limit']):
            data.update({'error': f'{self.TASK_NAME}: A required is not set. Cannot find properties.'})
            return not success, data

        realty_in_us = externals.RealtyInUsAPI(self.realty_in_us_config)
        response, data = realty_in_us.list_for_sale(params=self.realty_in_us_params)

        if response != 200:
            return False, {'error': f'{self.TASK_NAME}: {realty_in_us.name}: {str(response)}: {data}'}

        properties = []
        for prop in data['properties']:
            updated = datetime.datetime.strptime(prop['last_update'], '%Y-%m-%dT%H:%M:%SZ')
            if (updated + datetime.timedelta(hours=1)) < self.last_run:
                continue

            formatted_prop = {
                'property_id': prop['property_id'],
                'listing_id': prop['listing_id'],
                'link': prop['rdc_web_url'],
                'prop_type': prop['prop_type'],
                'address': prop['address'],
                'address_formatted': prop['address']['line'] + ', ' + prop['address']['city'] + ' ' + \
                                     prop['address']['state_code'] + ', ' + prop['address']['postal_code'],
                'price': prop['price'],
                'beds': prop['beds'],
                'baths': prop['baths'],
                'agents': prop['agents'],
                'office': prop['office'],
                'last_update': prop['last_update'],
                'mls': prop['mls']
            }

            properties.append(formatted_prop)

        """
        GET AREA INFORMATION

        Things needed right now are taxes, insurance?
        """

        us_real_estate = externals.UsRealEstateAPI(self.us_real_estate_config)
        response, data = us_real_estate.get_average_rates(params=self.us_real_estate_params)

        if response != 200:
            return False, {'error': f'{self.TASK_NAME}: {us_real_estate.name}: {str(response)}: {data}'}

        data = data['data']

        area = {
            'average_rent': data['average_rent_price'],
            'reference_price': data['reference_price'],
            'average_mortgage_rate': data['mortgage_data']['average_rate'],
            'insurance_rate': data['mortgage_data']['insurance_rate'],
            'property_tax_rate': data['mortgage_data']['property_tax']
        }

        """
        CALCULATE MORTGAGE PAYMENT
        """

        mortgage_crawler = externals.MortgageCalculatorCrawler(self.mortgage_calc_url)

        for prop in properties:
            term_dict = {
                'thirty': '30',
                'twenty': '20',
                'fifteen': '15',
                'ten': '10'
            }
            mortgage_params = {
                'homevalue': str(prop['price']),
                'downpayment': self.mortgage_params['downpayment'],
                'downpayment_type': self.mortgage_params['downpayment_type'],
                'interest_rate': str(area['average_mortgage_rate']['thirty_year_fha'])
                if self.mortgage_params['loan_type'] == 'fha' else
                str(area['average_mortgage_rate'][f'{self.mortgage_params["term"]}_year_fix']),
                'term': term_dict[self.mortgage_params['term']],
                'start_month': '0' + str(now.month),
                'start_year': str(now.year),
                'property_tax': str(float(area['property_tax_rate'])*int(prop['price'])),
                'pmi': str(self.mortgage_params['pmi']),
                'hoi': str(float(area['insurance_rate'])*int(prop['price'])),
                'hoa': '0',
                'milserve': '2' if self.mortgage_params['loan_type'] == 'fha' else '1',
                'refiorbuy': '1' if not self.mortgage_params['refi'] else '2',
                'credit_rating': '0',
                'draw_charts': '1'
            }

            if self.mortgage_params['downpayment_type'] == 'money':
                principal = str(int(prop['price']) - int(self.mortgage_params['downpayment']))
            else:
                principal = str(int(prop['price'])*(1-float(self.mortgage_params['downpayment'])))

            mortgage_params.update({'principal': principal})

            print(mortgage_params)

            mortgage_crawler.initiate_params(params=mortgage_params)
            monthly_payment = mortgage_crawler.run()
            print(monthly_payment)

        """
        CALCULATE KPIS
        
        What calculation? Traditional vs Reversed (rent)
        
        If Reversed, must GET ESTIMATED RENT FROM API
        """

        pass
