import argparse
import datetime
import os
import subprocess
import time

from dateutil.relativedelta import relativedelta

from qecommon_tools import safe_run, exit


PRESERVE_FILES_ARG = '--preserve-files'

VALID_UNITS = ['years', 'months', 'weeks', 'days']


def time_ago(unit, delta, start=None):
    start = start or datetime.date.today()
    return start - relativedelta(**{unit: delta})


def datetime_to_stamp(dt):
    return dt.strftime('%Y-%m-%d 23:59:59')


def subdirectory_path(output_path, date):
    return os.path.join(output_path, str(date))


def generate_rev_dates(args):
    first_date = datetime.date(1970, 1, 1)
    if hasattr(args, 'start_delta'):
        first_date = time_ago(args.start_unit, args.start_delta)
    cursor_date = datetime.date.today()
    while cursor_date > first_date:
        yield cursor_date
        cursor_date = time_ago(args.by_unit, 1, start=cursor_date)


def _prepare_coverage_args(coverage_args, output_dir, date):
    coverage_args.extend([
        '--output-dir', output_dir, '--timestamp', str(time.mktime(date.timetuple()))
    ])
    if PRESERVE_FILES_ARG not in coverage_args:
        coverage_args.append(PRESERVE_FILES_ARG)
    return coverage_args


def _allowed_units(unit):
    if not unit:
        return VALID_UNITS
    return VALID_UNITS[VALID_UNITS.index(unit) + 1:]


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


class SubordinateUnit(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        start_unit = args.start_unit
        if start_unit and values not in _allowed_units(start_unit):
            message = 'The `by-unit` ({}) must be smaller than the start unit ({})'
            raise ValueError(message.format(values, start_unit))
        setattr(args, self.dest, values)


def main():
    epilog = 'Must be run from the root of a repo with the full log history. (not `--depth 1`)'
    parser = argparse.ArgumentParser(
        description='Build historical coverage reports over a span of time.',
        epilog=epilog
    )
    parser.add_argument('--start-delta', action=StartUnit, dest='start_unit', default=None,
                        metavar='"<measure> <unit>"',
                        help='The space-separated (quoted) measure and unit '
                             'representing how far to look back in the repo history.'
                             ' The measure must be an integer.'
                             ' The unit must be one of: {}'
                             ' E.g. "5 weeks"'.format(VALID_UNITS))
    parser.add_argument('--by-unit', choices=VALID_UNITS, action=SubordinateUnit, default=None,
                        help='The unit of measure for the history increment "slices".'
                             ' Must be a smaller unit that the start unit.'
                             ' Default value is 1 unit of size smaller than the start unit '
                             ' or {} if no start unit provided.'.format(VALID_UNITS[0]))
    parser.add_argument('--output-dir', default='reports',
                        help='The relative path from repo root to store the reports.')
    args, coverage_args = parser.parse_known_args()
    depth = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'],
                                    universal_newlines=True).strip('\n')
    assert int(depth) > 1, 'History can not be run on a "thin" log: depth was {}'.format(depth)
    args.by_unit = args.by_unit or _allowed_units(args.start_unit)[0]
    output_path = os.path.abspath(args.output_dir)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    rev_dates = generate_rev_dates(args)
    for date in rev_dates:
        rev_command = [
            'git',
            'rev-list',
            '-n', '1',
            '--before="{}"'.format(datetime_to_stamp(date)),
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
        safe_run(_prepare_coverage_args(coverage_args, subdirectory_path(output_path, date), date))


if __name__ == '__main__':
    main()
