import argparse
import datetime
import os
import subprocess
import time

from dateutil.relativedelta import relativedelta

from qecommon_tools import safe_run, exit


PRESERVE_FILES_ARG = '--preserve-files'

TIMESTAMP_ARG = '--timestamp'

OUTPUT_DIR_ARG = '--output-dir'

VALID_UNITS = ['years', 'months', 'weeks', 'days']

DEFAULT_BY_UNIT = 'weeks'


def _time_ago(unit, delta, start=None):
    return (start or datetime.date.today()) - relativedelta(**{unit: delta})


def _subdirectory_path(output_path, date):
    return os.path.join(output_path, str(date))


def _generate_rev_dates(args):
    first_date = datetime.date.min
    if hasattr(args, 'start_delta'):
        first_date = _time_ago(args.start_unit, args.start_delta)
    cursor_date = datetime.date.today()
    while cursor_date > first_date:
        yield cursor_date
        cursor_date = _time_ago(args.by_unit, 1, start=cursor_date)


def _add_or_replace_arg(args_list, arg_key, arg_value):
    if arg_key in args_list:
        args_list[args_list.index(arg_key) + 1] = arg_value
    else:
        args_list.extend([arg_key, arg_value])
    return args_list


def _prepare_coverage_args(coverage_args, output_dir, date):
    _add_or_replace_arg(coverage_args, OUTPUT_DIR_ARG, output_dir)
    timestamp = str(time.mktime(date.timetuple()))
    _add_or_replace_arg(coverage_args, TIMESTAMP_ARG, timestamp)
    return coverage_args


class StartUnit(argparse.Action):
    def __call__(self, parser, args, value, option_string=None):
        values = value.split()
        if len(values) != 2:
            message = '`start-delta` should be only 2 items long (delta and unit): {}'
            raise ValueError(message.format(values))
        delta, unit = values
        if not delta.isdigit():
            raise ValueError('The `start-delta` delta must be an integer: {}'.format(delta))
        delta = int(delta)
        if unit not in VALID_UNITS:
            message = 'The `start-delta` unit {} was not one of: {}.'
            raise ValueError(message.format(unit, VALID_UNITS))
        setattr(args, 'start_delta', delta)
        setattr(args, 'start_unit', unit)


class SizeVerifiedUnit(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        start_unit = args.start_unit
        if start_unit and VALID_UNITS.index(values) < VALID_UNITS.index(start_unit):
            message = 'The `by-unit` ({}) must be no bigger than the start unit ({})'
            raise ValueError(message.format(values, start_unit))
        setattr(args, self.dest, values)


def main():
    epilog = 'Must be run from the root of a repo with the full log history. (not `--depth 1`)'
    parser = argparse.ArgumentParser(
        description='Build historical coverage reports over a span of time.', epilog=epilog
    )
    start_help = (
        'The space-separated (quoted) measure and unit representing how far back to look'
        ' in the repo history. The measure must be an integer.'
        ' The unit must be one of: {}. E.g. "5 weeks"'.format(VALID_UNITS)
    )
    parser.add_argument('--start-delta', action=StartUnit, dest='start_unit', default=None,
                        metavar='"<measure> <unit>"', help=start_help)
    by_help = (
        'The unit of measure for the history increment "slices".'
        ' Must be a unit no bigger than the start unit.'
    )
    parser.add_argument('--by-unit', choices=VALID_UNITS, action=SizeVerifiedUnit,
                        default=DEFAULT_BY_UNIT, help=by_help)
    parser.add_argument('--output-dir', default='reports',
                        help='The relative path from repo root to store the reports.')
    args, coverage_args = parser.parse_known_args()
    assert coverage_args, 'No coverage script/args were provided to run after checkout!'
    depth = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'],
                                    universal_newlines=True).strip('\n')
    assert int(depth) > 1, 'History can not be run on a "thin" log: depth was {}'.format(depth)
    output_path = os.path.abspath(args.output_dir)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    for date in _generate_rev_dates(args):
        rev_command = [
            'git',
            'rev-list',
            '-n', '1',
            '--before="{:%Y-%m-%d 23:59:59}"'.format(date),
            'master'
        ]
        rev = subprocess.check_output(rev_command, universal_newlines=True).strip('\n')
        if not rev:
            exit(message='No rev found before date: {}'.format(date))
        checkout_command = [
            'git',
            'checkout',
            rev
        ]
        safe_run(checkout_command)
        safe_run(_prepare_coverage_args(coverage_args, _subdirectory_path(output_path, date), date))


if __name__ == '__main__':
    main()
