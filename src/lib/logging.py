from datetime import datetime


class Log:

    def ok(self, message, data=None):
        print(f"INFO: {message} | {str(datetime.now())}")

    def error(self, message, data=None):
        print(f"ERROR: {message} | {str(datetime.now())}")