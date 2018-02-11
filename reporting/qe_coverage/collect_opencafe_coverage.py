#!/usr/bin/env python
'''
Run OpenCAFE command in a mode that collects coverage data and send it to splunk.
'''

import argparse
import glob
import os
import shutil
import subprocess
import sys
from tempfile import mkdtemp

from qecommon_tools import cleanup_and_exit, safe_run

TAGS_DIR_ENV_NAME = 'COLLECT_TAGS_DATA_INTO'


def main():
    parser = argparse.ArgumentParser(description='Collect and Publish OpenCAFE Coverage Report')
    parser.add_argument('--preserve-files', default=False, action='store_true',
                        help='Preserve report files generated')
    parser.add_argument('--dry-run', default=False, action='store_true',
                        help='Gather metrics, but do not send to splunk.')
    parser.add_argument('--leading-categories-to-strip', type=int, default=0,
                        help='The number of leading categories to omit from the coverage data '
                             'sent to Splunk')

    parser.add_argument('default_interface_type', choices='gui api'.split(),
                        help='The interface type of the product '
                             'if it is not otherwise specified or in the category list')
    # NOTE: This is a temporary work-around, each coverage file's line has a product available,
    #       but since we have multiple product right now, the reporting code needs to be expanded
    #       to handle that use case. QGTM-671 is tracking this.
    parser.add_argument('product_name',
                        help='The name of the product')
    parser.add_argument('open_cafe_command', nargs='+',
                        help='OpenCAFE command and parameters for running the tests')
    args, coverage_kwargs = parser.parse_known_args()

    tmp_dir_name = mkdtemp()

    os.environ[TAGS_DIR_ENV_NAME] = tmp_dir_name

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

    json_coverage_file = json_coverage_files[0]

    publish_command = [
        'coverage-send-opencafe-report',
        '-o', tmp_dir_name,
        '--leading-categories-to-strip', str(args.leading_categories_to_strip),
    ]
    if args.check_only:
        publish_command += ['--dry-run']
    publish_command += [
        json_coverage_file,
        args.product_name,
        args.default_interface_type,
    ]

    safe_run(publish_command)

    if args.preserve_files:
        print('Generated files located at: {}'.format(tmp_dir_name))
        tmp_dir_name = None
    cleanup_and_exit(dir_name=tmp_dir_name)


if __name__ == '__main__':
    main()
