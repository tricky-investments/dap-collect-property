from dotenv import load_dotenv
from optparse import OptionParser
import os

from lib import logging
from property import main as collect

load_dotenv()


def main():
    settings = collect.set_settings()
    opt_parser = OptionParser()
    grab_options(opt_parser)
    collect.grab_collector_options(opt_parser)
    (options, args) = opt_parser.parse_args()

    log = logging.Log()
    collector = collect.Collector(log=log)

    if options.development:
        # This is a development run
        collector.run_dev(options=options, settings=settings)


def grab_options(parser: OptionParser):
    parser.add_option('-d', action='store_true', default=False, dest='development')


if __name__ == '__main__':
    main()
