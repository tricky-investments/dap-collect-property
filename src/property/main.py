import json
from optparse import OptionParser
import os
import requests

from property import tasks
from tricky_alert import email_type
from tricky_alert.instance import EmailInstance

COLLECTOR_NAME = 'property'
COLLECTOR_DIRECTORY = 'property'


def grab_collector_options(parser: OptionParser):
    parser.add_option('-l', '--price_min', action='store', type='int', dest='price_min')
    parser.add_option('-h', '--price_max', action='store', type='int', dest='price_max')
    parser.add_option('-t', '--prop_type', action='store', dest='prop_type')
    parser.add_option('f', '--features', action='append', dest='features')
    parser.add_option('-a', '--city', action='store', dest='city')
    parser.add_option('-s', '--state_code', action='store', dest='state_code')
    parser.add_option('--offset', action='store', dest='offset')
    parser.add_option('--limit', action='store', dest='limit')
    # MORTGAGE OPTIONS HERE
    parser.add_option('-c', '-calculation', action='store', dest='calculation', default='traditionals')
    parser.add_option('--cap_rate', action='store', dest='cap_rate')
    parser.add_option('--monthly_income', action='store', dest='monthly_income')
    parser.add_option('--roi', action='store', dest='roi')
    parser.add_option('--grm', action='store', dest='grm')
    parser.add_option('--rpr', action='store', dest='rpr')


def set_settings():
    settings = {
        'realty_in_us_config': {
            'realty_in_us_host': os.getenv('REALTY_IN_US_HOST'),
            'realty_in_us_key': os.getenv('REALTY_IN_US_KEY')
        },
        'us_real_estate_config': {
            'us_real_estate_host': os.getenv('US_REAL_ESTATE_HOST'),
            'us_real_estate_key': os.getenv('US_REAL_ESTATE_KEY')
        },
        'tricky_alert_config': {
            'receiver_emails': json.loads(os.getenv('RECEIVER_EMAILS')),
            'sender_email': os.getenv('SENDER_EMAIL'),
            'sender_pass': os.getenv('SENDER_PASS')
        }
    }

    return settings


class Collector:

    def __init__(self, log):
        self.name = COLLECTOR_NAME
        self.log = log

    def generate_tasks(self, options):

        if options.__dict__()['job_type'] is None:
            return None

        if options.job_type == 'search':
            search_task = tasks.search.SearchPropertiesTask(log=self.log, collector=self)
            process_task = tasks.process.ProcessPropertiesTask(log=self.log, collector=self)

        return [search_task, process_task]

    def report_error(self, data):

        sender = email_type.sender.Sender(os.getenv('SENDER_EMAIL'), os.getenv('SENDER_PASS'))
        receiver = email_type.sender.Sender('troy.fintech@gmail.com')
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
