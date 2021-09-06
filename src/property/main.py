import json
from optparse import OptionParser
import os
import requests

from tricky_alert import email_type
from tricky_alert.instance import EmailInstance


COLLECTOR_NAME = 'property'
COLLECTOR_DIRECTORY = 'property'


def grab_collector_options(parser: OptionParser):
    parser.add_option('-p', '--price', action='store', type='int', dest='price')
    parser.add_option('-t', '--type', action='store', dest='type')
    parser.add_option('-a', '--area', action='store', dest='area')


def set_settings():
    settings = {
        'rapidapi_host': os.getenv('X_RAPIDAPI_HOST'),
        'rapidapi_key': os.getenv('X_RAPIDAPI_KEY')
    }

    return settings


class Collector:

    def __init__(self, log):
        self.name = COLLECTOR_NAME
        self.log = log
        pass

    def generate_tasks(self, options, settings):
        pass

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

        sender = email_type.sender.Sender('TEST', 'TEST')
        receiver = email_type.receiver.Receiver('TEST', 'Troy', 'Stanich')
        instance = EmailInstance(sender)
        instance.add_recipients([receiver])

        for prop in data['properties']:
            email = email_type.Email('Property Found', prop['property_id'], [prop['rdc_web_url']])
            instance.send_all(email)
