#!/usr/bin/env python
'''
Run OpenCAFE command in a mode that collects coverage data and send it to splunk.
'''

import glob
import os
import sys
from tempfile import mkdtemp

from qecommon_tools import cleanup_and_exit, safe_run
from qe_coverage.base import build_opencafe_parser

TAGS_DIR_ENV_NAME = 'COLLECT_TAGS_DATA_INTO'


def main():
    parser = build_opencafe_parser('Collect and publish OpenCAFE coverage report')
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
        '--host', args.host,
        '--leading-categories-to-strip', str(args.leading_categories_to_strip),
    ]
    if args.dry_run:
        publish_command += ['--dry-run']
    publish_command += [
        args.default_interface_type,
        args.product_name,
        json_coverage_file,
    ]

    safe_run(publish_command)

    if args.preserve_files:
        print('Generated files located at: {}'.format(tmp_dir_name))
        tmp_dir_name = None
    cleanup_and_exit(dir_name=tmp_dir_name)


if __name__ == '__main__':
    main()
