import datetime
import os
from abc import ABC

from .helpers import calculator, externals

from lib.abstract import Task


def export_last_run(app_data_path, dt):
    string_dt = str(dt)
    with open(os.path.join(app_data_path, 'last_run.txt'), 'w') as f:
        f.write(string_dt)


class SearchPropertiesTask(Task):
    TASK_NAME = "Property Search Task"

    def __str__(self):
        return self.TASK_NAME

    def load_settings(self, settings):
        self.realty_in_us_config = settings['realty_in_us_config']
        self.us_real_estate_config = settings['us_real_estate_config']
        self.mortgage_calc_url = settings['mortgage_calc_url']
        self.app_data_path = settings['app_data_path']
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
        keys = ['downpayment', 'downpayment_type', 'term', 'pmi', 'loan_type', 'refi']
        for key in keys:
            if key in params.keys():
                self.mortgage_params.update({key: params[key]})

        self.expenses = {}
        keys = ['closing_cost', 'vacancy_rate', 'repair_rate', 'management_rate', 'capex_rate', 'electric', 'water', 'gas']
        for key in keys:
            if key in params.keys():
                self.expenses.update({key: params[key]})

        self.kpis = {}
        keys = ['calculation', 'cap_rate', 'monthly_income', 'roi', 'grm', 'rpr']
        for key in keys:
            if key in params.keys():
                self.kpis.update({key: params[key]})

    def _update_last_run(self, now):
        with open(os.path.join(self.app_data_path, 'last_run.txt'), 'w') as f:
            f.write(str(now))

    def run(self):

        success = True
        data = {}
        """
        COLLECT PROPERTIES

        Use Realty in US API to collect properties from Realtor.com
        """
        self.log.ok('Getting property data.')
        now = datetime.datetime.now()

        if not all(i in self.realty_in_us_params.keys() for i in ['city', 'state_code', 'offset', 'limit']):
            data.update({'error': f'{self.TASK_NAME}: A required is not set. Cannot find properties.'})
            return not success, data

        realty_in_us = externals.RealtyInUsAPI(self.realty_in_us_config)
        response, data = realty_in_us.list_for_sale(params=self.realty_in_us_params)

        if response != 200:
            return False, {'error': f'{self.TASK_NAME}: {realty_in_us.name}: {str(response)}: {data}'}

        export_last_run(self.app_data_path, datetime.datetime.now())
        self.log.ok(f'Retrieved property data from {realty_in_us.API_NAME}.')

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

        self._update_last_run(now)

        self.log.ok('Formatted property data.')

        """
        GET AREA INFORMATION

        Things needed right now are taxes, insurance?
        """
        self.log.ok('Getting area data.')

        us_real_estate = externals.UsRealEstateAPI(self.us_real_estate_config)
        response, data = us_real_estate.get_average_rates(params=self.us_real_estate_params)

        if response != 200:
            return False, {'error': f'{self.TASK_NAME}: {us_real_estate.name}: {str(response)}: {data}'}

        self.log.ok(f'Retrieved area data from {us_real_estate.API_NAME}.')
        data = data['data']

        area = {
            'average_rent': data['average_rent_price'],
            'reference_price': data['reference_price'],
            'average_mortgage_rate': data['mortgage_data']['average_rate'],
            'insurance_rate': data['mortgage_data']['insurance_rate'],
            'property_tax_rate': data['mortgage_data']['property_tax']
        }

        self.log.ok('Formatted area data.')
        """
        CALCULATE MORTGAGE PAYMENT
        """
        self.log.ok('Calculating mortgage payments.')

        mortgage_crawler = externals.MortgageCalculatorCrawler(self.mortgage_calc_url)

        for prop in properties:

            self.log.ok(f'Calculating mortgage for {prop["address_formatted"]}.')
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
                'property_tax': str(float(area['property_tax_rate']) * int(prop['price'])),
                'pmi': str(self.mortgage_params['pmi']),
                'hoi': str(float(area['insurance_rate']) * int(prop['price'])),
                'hoa': '0',
                'milserve': '2' if self.mortgage_params['loan_type'] == 'fha' else '1',
                'refiorbuy': '1' if not self.mortgage_params['refi'] else '2',
                'credit_rating': '0',
                'draw_charts': '1'
            }

            if self.mortgage_params['downpayment_type'] == 'money':
                principal = str(int(prop['price']) - int(self.mortgage_params['downpayment']))
            else:
                principal = str(int(prop['price']) * (1 - float(self.mortgage_params['downpayment'])))

            mortgage_params.update({'principal': principal})

            mortgage_crawler.initiate_params(params=mortgage_params)
            monthly_payment = mortgage_crawler.run()
            prop['mortgage'] = monthly_payment

        self.log.ok('Calculated Mortgage payments.')
        """
        CALCULATE KPIS
        
        What calculation? Traditional vs Reversed (rent)
        
        If Reversed, must GET ESTIMATED RENT FROM API
        """

        if self.kpis['calculation'] == 'traditional':
            return False, {'error': 'Traditional calculations not implemented.'}

        process_data = {
            'area_data': {
                'City': self.realty_in_us_params['city'],
                'State': self.realty_in_us_params['state_code'],
                'Postal Code': self.us_real_estate_params['postal_code'],
                'Mortgage Rate': area['average_mortgage_rate']['thirty_year_fha'],
                'Insurance Rate': area['insurance_rate'],
                'Property Tax Rate': area['property_tax_rate']
            },
            'mortgage_params': {
                'Downpayment': self.mortgage_params['downpayment'],
                'Downpayment Type': self.mortgage_params['downpayment_type'],
                'Term': self.mortgage_params['term'],
                'PMI': self.mortgage_params['pmi'],
                'Loan Type': self.mortgage_params['loan_type'],
                'Refinance?': 'Yes' if self.mortgage_params['refi'] else 'No'
            },
            'expected_expenses': {
                'Vacancy Rate': self.expenses['vacancy_rate'],
                'Repair Rate': self.expenses['repair_rate'],
                'Management Rate': self.expenses['management_rate'],
                'CapEx Rate': self.expenses['capex_rate'],
                'Electric': self.expenses['electric'],
                'Water': self.expenses['water'],
                'Gas': self.expenses['gas'],
                'Closing Costs': self.expenses['closing_cost']
            },
            'required_kpis': {
                'Cap Rate': self.kpis['cap_rate'],
                'Monthly Income': self.kpis['monthly_income'],
                'Cash on Cash ROI': self.kpis['roi'],
                'Growth Rent Multiplier': self.kpis['grm'],
                'RPR': self.kpis['rpr']
            },
            'properties': []
        }

        for prop in properties:
            calc_data = {
                'purchase_price': float(prop['price']),
                'downpayment': float(self.mortgage_params['downpayment']) if self.mortgage_params[
                                                                                 'downpayment_type'] == 'money'
                else float(self.mortgage_params['downpayment']) * float(prop['price']),
                'closing_cost': float(self.expenses['closing_cost']) * float(prop['price']),
                'mortgage': prop['mortgage'],
                'vacancy_rate': float(self.expenses['vacancy_rate']),
                'repair_rate': float(self.expenses['repair_rate']),
                'capex_rate': float(self.expenses['capex_rate']),
                'management_rate': float(self.expenses['management_rate']),
                'electric': float(self.expenses['electric']),
                'water': float(self.expenses['water']),
                'gas': float(self.expenses['gas']),
                'monthly_income': float(self.kpis['monthly_income']) if self.kpis['monthly_income'] is not None else None,
                'cap_rate': float(self.kpis['cap_rate']) if self.kpis['cap_rate'] is not None else None,
                'roi': float(self.kpis['roi']) if self.kpis['roi'] is not None else None,
                'grm': float(self.kpis['grm']) if self.kpis['grm'] is not None else None,
                'rpr': float(self.kpis['rpr']) if self.kpis['rpr'] is not None else None,
            }

            kpis = calculator.traditional_reversed_rent(calc_data)

            process_prop = {
                'Address': prop['address_formatted'],
                'Property Type': prop['prop_type'],
                'Price': prop['price'],
                'Beds': prop['beds'],
                'Baths': prop['baths'],
                'MLS Name': prop['mls']['name'],
                'MLS ID': prop['mls']['id'],
                'Estimated Mortgage': prop['mortgage'],
                'Closing Costs': float(self.expenses['closing_cost'])*float(prop['price']),
                'link': prop['link']
            }

            if self.mortgage_params['downpayment_type'] == 'money':
                process_prop.update({'Downpayment': self.mortgage_params['downpayment']})
            else:
                process_prop.update({'Downpayment': float(self.mortgage_params['downpayment'])*float(prop['price'])})

            for kpi in kpis:
                if kpi == 'cap_rate':
                    process_prop.update({'Cap Rate': kpis[kpi]})
                if kpi == 'roi':
                    process_prop.update({'Cash on Cash ROI': kpis[kpi]})
                if kpi == 'monthly_income':
                    process_prop.update({'Monthly Income': kpis[kpi]})
                if kpi == 'grm':
                    process_prop.update({'Growth Rent Multiplier': kpis[kpi]})
                if kpi == 'rpr':
                    process_prop.update({'RPR': kpis[kpi]})

            process_data['properties'].append(process_prop)

        return success, process_data
