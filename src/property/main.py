import json
from optparse import OptionParser
import os
import requests

from .tasks import search, process
from tricky_alert import email_type
from tricky_alert.instance import EmailInstance

COLLECTOR_NAME = 'property'
COLLECTOR_DIRECTORY = 'property'


def grab_collector_options(parser: OptionParser):
    parser.add_option('--price_min', action='store', type='int', dest='price_min')
    parser.add_option('--price_max', action='store', type='int', dest='price_max')
    parser.add_option('--prop_type', action='store', dest='prop_type')
    parser.add_option('--features', action='append', dest='features')
    parser.add_option('--city', action='store', dest='city')
    parser.add_option('--state_code', action='store', dest='state_code')
    parser.add_option('--offset', action='store', dest='offset')
    parser.add_option('--limit', action='store', dest='limit')
    parser.add_option('--postal_code', action='store', dest='postal_code')

    # MORTGAGE OPTIONS HERE
    parser.add_option('--downpayment', action='store', dest='downpayment')
    parser.add_option('--dp_type', action='store', dest='downpayment_type')
    parser.add_option('--term', action='store', dest='term')
    parser.add_option('--pmi', action='store', dest='pmi')
    parser.add_option('--loan_type', action='store', dest='loan_type')
    parser.add_option('--refi', action='store_true', default=False, dest='refi')

    # EXPENSES HERE
    parser.add_option('--vacancy', action='store', dest='vacancy_rate')
    parser.add_option('--repair', action='store', dest='repair_rate')
    parser.add_option('--management', action='store', dest='management_rate')
    parser.add_option('--capex', action='store', dest='capex_rate')
    parser.add_option('--elec', action='store', dest='electric')
    parser.add_option('--water', action='store', dest='water')
    parser.add_option('--gas', action='store', dest='gas')
    parser.add_option('--closing_cost', action='store', dest='closing_cost')

    # CALCULATION OPTIONS HERE
    parser.add_option('--calculation', action='store', dest='calculation', default='traditionals')
    parser.add_option('--cap_rate', action='store', dest='cap_rate')
    parser.add_option('--monthly_income', action='store', dest='monthly_income')
    parser.add_option('--roi', action='store', dest='roi')
    parser.add_option('--grm', action='store', dest='grm')
    parser.add_option('--rpr', action='store', dest='rpr')


def set_settings():
    settings = {
        'realty_in_us_config': {
            'x-rapidapi-host': os.getenv('REALTY_IN_US_HOST'),
            'x-rapidapi-key': os.getenv('REALTY_IN_US_KEY')
        },
        'us_real_estate_config': {
            'x-rapidapi-host': os.getenv('US_REAL_ESTATE_HOST'),
            'x-rapidapi-key': os.getenv('US_REAL_ESTATE_KEY')
        },
        'tricky_alert_config': {
            'receiver_emails': json.loads(os.getenv('RECEIVER_EMAILS')),
            'sender_email': os.getenv('SENDER_EMAIL'),
            'sender_pass': os.getenv('SENDER_PASS')
        },
        'mortgage_calc_url': os.getenv('MORTGAGE_CALCULATOR_URL'),
        'zillow_url': os.getenv('ZILLOW_URL'),
        'last_run': os.getenv('LAST_RUN'),
        'app_data_path': os.getenv('APP_DATA_PATH'),
        'log_file': os.getenv('LOG_FILE')
    }

    return settings


class Collector:

    def __init__(self, log):
        self.name = COLLECTOR_NAME
        self.log = log

    def generate_tasks(self, options):

        if options.__dict__['task_type'] is None:
            return None

        if options.task_type == 'search':
            search_task = search.SearchPropertiesTask(log=self.log, collector=self)
            process_task = process.ProcessPropertiesTask(log=self.log, collector=self)

        return [search_task, process_task]  # , process_task]

    def report_error(self, data):

        sender = email_type.sender.Sender(os.getenv('SENDER_EMAIL'), os.getenv('SENDER_PASS'))
        receiver = email_type.receiver.Receiver('troy.fintech@gmail.com', 'Troy', 'Stanich')
        instance = EmailInstance(sender)
        instance.add_recipients([receiver])
        email = email_type.Email(f"Error with {self.name} Collector", data['error'])
        try:
            instance.send_all(email)
        except Exception as e:
            self.log.error(str(e))

    def run_dev(self, options, settings):

        if options.__dict__['area'] is None:
            self.log.error('Area option cannot be empty.')

        if options.__dict__['price'] is None:
            self.log.error('Price option cannot be empty.')

        url = 'https://' + settings['rapidapi_host'] + '/properties/v2/list-for-sale'
        querystring = {
            'city': options.area,
            'state_code': 'NJ',
            'offset': '0',
            'limit': '200',
            'sort': 'price_low',
            'price_max': str(options.price)
        }
        if options.__dict__['type'] is not None:
            querystring['prop_type'] = options.type

        headers = {
            'x-rapidapi-host': settings['rapidapi_host'],
            'x-rapidapi-key': settings['rapidapi_key']
        }

        response = requests.request('GET', url, headers=headers, params=querystring)
        data = json.loads(response.text)

        sender = email_type.sender.Sender('trickyinvestments@gmail.com', 'TIpassword4G')
        receiver = email_type.receiver.Receiver('troy.fintech@gmail.com', 'Troy', 'Stanich')
        instance = EmailInstance(sender)
        instance.add_recipients([receiver])

        for prop in data['properties']:
            email = email_type.Email('Property Found', prop['property_id'], [prop['rdc_web_url']])
            instance.send_all(email)
