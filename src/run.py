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

    log = logging.Log(settings['log_file'])
    collector = collect.Collector(log=log)

    if options.development:
        # This is a development run
        collector.run_dev(options=options, settings=settings)
        exit()

    plan = collector.generate_tasks(options=options)
    data = vars(options)

    if isinstance(plan, list):
        for task in plan:
            try:
                task.load_settings(settings=settings)
                task.load_parameters(params=data)
                success, data = task.run()

                if not success:
                    collector.report_error(data)
                    break

            except Exception as e:
                log.error(str(e))
                collector.report_error({'error': str(e)})
                break

    elif plan is not None:
        try:
            plan.load_settings(settings=settings)
            plan.load_parameters(params=data)
            success, data = plan.run()

            if not success:
                collector.report_error(data)

        except Exception as e:
            log.error(str(e))
            collector.report_error({'error': str(e)})

    log.commit()


def grab_options(parser: OptionParser):
    parser.add_option('-d', action='store_true', default=False, dest='development')
    parser.add_option('-t', action='store', dest='task_type')


if __name__ == '__main__':
    main()
