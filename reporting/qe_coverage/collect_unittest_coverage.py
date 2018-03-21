#!/usr/bin/env python
'''
Run Unittest or OpenCAFE command in a mode that collects coverage data and send it to splunk.
'''

import argparse
import glob
import os
import sys
from tempfile import mkdtemp

from qecommon_tools import safe_run
from qe_coverage.base import update_parser
from qe_coverage.send_unittest_tags_report import run_unittest_reports

TAGS_DIR_ENV_NAME = 'COLLECT_TAGS_DATA_INTO'


def main():
    _method = ''
    # Determine how this is called, whether it's for unittest or opencafe based on the
    # script used
    calling_script = os.path.basename(sys.argv[0])
    if 'unittest' in calling_script:
        _method = 'Unittest'
    elif 'opencafe' in calling_script:
        _method = 'OpenCAFE'

    epilog = 'Note: Run this script from the root of the test tree being reported on'
    description = 'Collect and publish {} coverage report'
    parser = argparse.ArgumentParser(description=description.format(_method),
                                     epilog=epilog)
    parser = update_parser(parser)
    parser.add_argument('command', nargs='+',
                        help='{} command and parameters for running the tests'.format(_method))
    args, coverage_kwargs = parser.parse_known_args()
    kwargs = vars(args)

    tmp_dir_name = mkdtemp()

    os.environ[TAGS_DIR_ENV_NAME] = kwargs['output_dir'] = tmp_dir_name

    args.command.extend(coverage_kwargs)
    safe_run(args.command)

    json_coverage_files = glob.glob('{}/*.json'.format(tmp_dir_name))

    if not json_coverage_files:
        print('')
        print('Error: No JSON report generated!')
        print('       {} command: {}'.format(_method, ' '.join(args.command)))
        sys.exit(-2)

    if len(json_coverage_files) != 1:
        print('')
        print('Error: Too many coverage files found!')
        print('       {}'.format(' '.join(json_coverage_files)))
        sys.exit(-3)

    del kwargs['command']  # Only needed for running test runner
    run_unittest_reports(json_coverage_files[0], kwargs.pop('product_hierarchy'),
                         kwargs.pop('default_interface_type'), **kwargs)


if __name__ == '__main__':
    main()
