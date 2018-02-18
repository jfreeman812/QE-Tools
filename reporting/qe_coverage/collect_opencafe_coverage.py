#!/usr/bin/env python
'''
Run OpenCAFE command in a mode that collects coverage data and send it to splunk.
'''

import argparse
import glob
import os
import sys
from tempfile import mkdtemp

from qecommon_tools import safe_run
from qe_coverage.base import update_parser
from qe_coverage.send_opencafe_tags_report import run_opencafe_reports

TAGS_DIR_ENV_NAME = 'COLLECT_TAGS_DATA_INTO'


def main():
    epilog = 'Note: Run this script from the root of the test tree being reported on'
    parser = argparse.ArgumentParser(description='Collect and publish OpenCAFE coverage report',
                                     epilog=epilog)
    parser = update_parser(parser)
    parser.add_argument('open_cafe_command', nargs='+',
                        help='OpenCAFE command and parameters for running the tests')
    args, coverage_kwargs = parser.parse_known_args()
    kwargs = vars(args)

    tmp_dir_name = mkdtemp()

    os.environ[TAGS_DIR_ENV_NAME] = kwargs['output_dir'] = tmp_dir_name

    args.open_cafe_command.extend(coverage_kwargs)
    safe_run(args.open_cafe_command)

    json_coverage_files = glob.glob('{}/*.json'.format(tmp_dir_name))

    if not json_coverage_files:
        print('')
        print('Error: No JSON report generated!')
        print('       OpenCAFE command: {}'.format(' '.join(args.open_cafe_command)))
        sys.exit(-2)

    if len(json_coverage_files) != 1:
        print('')
        print('Error: Too many coverage files found!')
        print('       {}'.format(' '.join(json_coverage_files)))
        sys.exit(-3)

    del kwargs['open_cafe_command']  # Only needed for running OpenCAFE
    run_opencafe_reports(json_coverage_files[0], kwargs.pop('default_interface_type'),
                         kwargs.pop('product_hierarchy'), **kwargs)


if __name__ == '__main__':
    main()
