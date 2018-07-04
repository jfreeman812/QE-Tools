import argparse
from csv import DictReader
import os

from qecommon_tools import exit as _exit
from qecommon_tools import safe_run


def _run_reports(builder_args, additional_args):
    csv_file = builder_args.coverage_csv_file
    no_cs = 'Missing coverage_script from command line or CSV file: "{}"'.format(csv_file)
    no_dit = 'Missing default_interface_type from command line or CSV file: "{}"'.format(csv_file)
    no_ph = 'Missing product_hierarchy column from CSV file: "{}"'.format(csv_file)

    with open(csv_file, 'r') as csvfile:
        for row in DictReader(csvfile, skipinitialspace=True):
            coverage_script = row.pop('coverage_script', builder_args.coverage_script)
            if coverage_script is None:
                _exit(1, no_cs)

            default_interface_type = row.pop('default_interface_type',
                                             builder_args.default_interface_type)
            if default_interface_type is None:
                _exit(1, no_dit)

            product_hierarchy = row.pop('product_hierarchy', None)
            if product_hierarchy is None:
                _exit(1, no_ph)

            coverage_command = [
                coverage_script,
                default_interface_type,
                product_hierarchy,
            ]
            for key, value in ((k, v) for k, v in row.items() if v):
                    coverage_command.extend(['--{}'.format(key), value])
            coverage_command.extend(additional_args)
            safe_run(coverage_command)


def _get_parser():
    epilog = (
        'CSV Files must contain the "product_hierarchy" column/value.'
        ' Any additional columns (such as "product_dir") will be passed to the coverage script'
        ' Example: "--product_dir this/is/a/row/value"'
        ' All other args flow through to the coverage script.'
    )
    parser = argparse.ArgumentParser(
        'Run coverage reports using a csv file of product data',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=epilog
    )
    parser.add_argument('coverage_csv_file',
                        help='The path to the csv containing product data.')
    parser.add_argument('coverage_script', nargs='?',
                        help='The coverage script to be run, if not specified in the CSV file.')
    parser.add_argument('default_interface_type', nargs='?', choices=['api', 'gui'],
                        help='The interface type of the product, if not specified in the CSV file.')
    return parser


def main():
    parser = _get_parser()
    builder_args, additional_args = parser.parse_known_args()
    _run_reports(builder_args, additional_args)


if __name__ == '__main__':
    main()
