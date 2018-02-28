import argparse
import datetime
import os
import subprocess
import time

from dateutil.relativedelta import relativedelta

from qecommon_tools import safe_run


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
    first_date = time_ago(args.start_unit, args.start_delta)
    cursor_date = datetime.date.today()
    dates_to_report = []
    while cursor_date > first_date:
        dates_to_report.append(cursor_date)
        cursor_date = time_ago(args.by_unit, 1, start=cursor_date)
    return dates_to_report


def _prepare_coverage_args(coverage_args, output_dir, date):
    coverage_args.extend([
        '--output-dir', output_dir, '--timestamp', str(time.mktime(date.timetuple()))
    ])
    if PRESERVE_FILES_ARG not in coverage_args:
        coverage_args.append(PRESERVE_FILES_ARG)
    return coverage_args


def _allowed_units(unit):
    return VALID_UNITS[VALID_UNITS.index(unit) + 1:]


class SubordinateUnit(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        start_unit = args.start_unit
        if values not in _allowed_units(start_unit):
            message = 'The by unit ({}) must be smaller than the start unit ({})'
            raise ValueError(message.format(values, start_unit))
        setattr(args, self.dest, values)


def main():
    epilog = 'Must be run from the root of a repo with the full log history. (not `--depth 1`)'
    parser = argparse.ArgumentParser(
        description='Build historical coverage reports over a span of time.',
        epilog=epilog
    )
    parser.add_argument('start_delta', type=int,
                        help='Integer representing the number of "start_unit"s to reach back to.')
    parser.add_argument('start_unit', choices=VALID_UNITS,
                        help='The unit of measure for how far back to start')
    parser.add_argument('--by-unit', choices=VALID_UNITS, action=SubordinateUnit, default=None,
                        help='The unit of measure for the history increment "slices".'
                             ' Must be a smaller unit that the start unit.'
                             ' Default value is 1 unit of size smaller than the start unit.')
    parser.add_argument('--output-dir', default='reports')
    args, coverage_args = parser.parse_known_args()
    args.by_unit = args.by_unit or _allowed_units(args.start_unit)[0]
    if VALID_UNITS.index(args.by_unit) <= VALID_UNITS.index(args.start_unit):
        message = 'The by unit ({}) must be smaller than the start unit ({})'
        raise ValueError(message.format(args.by_unit, args.start_unit))
    output_path = os.path.abspath(args.output_dir)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    for date in generate_rev_dates(args):
        rev_command = [
            'git',
            'rev-list',
            '-n', '1',
            '--before="{}"'.format(datetime_to_stamp(date)),
            'master'
        ]
        rev = subprocess.check_output(rev_command, universal_newlines=True).strip('\n')
        assert rev, 'No rev found in log before "{}"'.format(date)
        checkout_command = [
            'git',
            'checkout',
            rev
        ]
        safe_run(checkout_command)
        safe_run(_prepare_coverage_args(coverage_args, subdirectory_path(output_path, date), date))


if __name__ == '__main__':
    main()
