from lib.abstract import Task


class ProcessPropertiesTask(Task):

    TASK_NAME = "Property Process Task"

    def __str__(self):
        return self.TASK_NAME

    def load_settings(self, settings):
        pass

    def load_parameters(self, params):
        pass

    def run(self):
        pass
