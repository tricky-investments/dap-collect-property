from datetime import datetime
import logging


class Log:
    def __init__(self, log_file):
        self.log_file = log_file
        self.lines = []

    def _write_line(self, level, message, time):

        line = '|'.join([level, message, time])
        print(line)
        self.lines.append(line)

    def commit(self):
        with open(self.log_file, 'w') as log:
            log.write('\n'.join(self.lines))

    def ok(self, message, data=None):
        self._write_line("info", message, str(datetime.now()))

    def warn(self, message, data=None):
        self._write_line("warn", message, str(datetime.datetime.now()))

    def error(self, message, data=None):
        self._write_line("error", message, str(datetime.now()))
