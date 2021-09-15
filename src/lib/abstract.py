from abc import abstractmethod


class Task:

    def __init__(self, log, collector):
        self.log = log
        self.collector = collector

    @abstractmethod
    def load_settings(self, settings):
        pass

    @abstractmethod
    def load_parameters(self, params):
        pass

    @abstractmethod
    def run(self):
        pass


class Api:

    def __init__(self, api_config):
        self.api_config = api_config

    @abstractmethod
    def _call_endpoint(self, method, endpoint, headers, params):
        pass
