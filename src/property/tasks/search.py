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

    def load_parameters(self, params):

        self.realty_in_us_params = {}
        keys = ['city', 'state_code', 'limit', 'offset', 'prop_type', 'features', 'price_min', 'price_max']
        for key in keys:
            if key in params.keys():
                self.realty_in_us_params.update({key: params['key']})

        self.params = params

    def run(self):

        success = True
        data = {}

        """
        COLLECT PROPERTIES

        Use Realty in US API to collect properties from Realtor.com
        """
        if not all(i in self.params.keys() for i in ['city', 'state_code', 'offset', 'limit']):
            data.update({'error': f'{self.TASK_NAME}: A required is not set. Cannot find properties.'})
            return not success, data

        realty_in_us = externals.RealtyInUsAPI(self.realty_in_us_config)


        """
        CALCULATE MORTGAGE PAYMENT
        """

        """
        GET AREA INFORMATION
        
        Things needed right now are taxes, insurance?
        """

        """
        CALCULATE KPIS
        
        What calculation? Traditional vs Reversed (rent)
        
        If Reversed, must GET ESTIMATED RENT FROM API
        """

        pass
