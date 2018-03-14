import argparse
from csv import DictReader
import os

from qecommon_tools import safe_run


def _run_reports(builder_args, additional_args):
    with open(builder_args.coverage_csv_file, 'r') as csvfile:
        for row in DictReader(csvfile):
            coverage_command = [
                builder_args.coverage_script,
                builder_args.default_interface_type,
                row['product_hierarchy'],
            ]
            if 'product_dir' in row:
                coverage_command.extend([
                    '-p',
                    row['product_dir']
                ])
            coverage_command.extend(additional_args)
            safe_run(coverage_command)


def _get_parser():
    epilog = (
        'CSV Files must contain the "product_hierarchy" value.'
        ' "product_dir" is supported but optional. All other columns are ignored.'
        ' All other args flow through to the coverage script.'
    )
    parser = argparse.ArgumentParser(
        'Run coverage reports using a csv file of product data',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=epilog
    )
    parser.add_argument('coverage_csv_file',
                        help='The path to the csv containing product data.')
    parser.add_argument('coverage_script',
                        help='The name of the coverage script to be run.')
    parser.add_argument('default_interface_type', choices=['api', 'gui'],
                        help='The interface type of the product if not otherwise specified.')
    return parser


def main():
    parser = _get_parser()
    builder_args, additional_args = parser.parse_known_args()
    _run_reports(builder_args, additional_args)


if __name__ == '__main__':
    main()
