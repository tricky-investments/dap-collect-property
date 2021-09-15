import json
import requests

from lib.abstract import Api


class RealtyInUsAPI(Api):
    API_NAME = "Realty in US Api (Realtor) from RapidApi"

    def _call_endpoint(self, method, endpoint, params):
        url = 'https://' + self.api_config['host'] + endpoint
        headers = {
            'x-rapidapi-host': self.api_config['host'],
            'x-rapidapi-key': self.api_config['api_key']
        }

        response = requests.request(method, url, headers=headers, params=params)
        return response.ok, json.loads(response.text)


class UsRealEstateAPI(Api):
    API_NAME = "US Real Estate Api from RapidApi"

    def _call_endpoint(self, method, endpoint, params):
        url = 'https://' + self.api_config['host'] + endpoint
        headers = {
            'x-rapidapi-host': self.api_config['host'],
            'x-rapidapi-key': self.api_config['api_key']
        }

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




