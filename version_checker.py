#! /usr/bin/env python

import glob
import os

from github_tools import GHPRSession, ghprb_info, get_github_commenter_parser


VERSION_FILE_NAME = '__version__.py'


def main():
    parser = get_github_commenter_parser('Docs link PR Commenter')
    args = parser.parse_args()
    repo = ghprb_info.repository
    pull_id = ghprb_info.pull_request_id
    domain = ghprb_info.domain

    gh = GHPRSession(args.token, domain, repo, pull_id)

    for version_file in glob.glob('**/{}'.format(VERSION_FILE_NAME), recursive=True):
        package = os.path.dirname(version_file)
        package_was_modified = bool(gh.get_diff(files=package))
        if package_was_modified:
            version_file_was_modified = bool(gh.get_diff(files=version_file))
            if not version_file_was_modified:
                gh.post_comment(
                    '### Warning\n'
                    '\n'
                    'You\'ve changed the contents of the `{package}` package, '
                    'but you did not update the version!\n'
                    '\n'
                    'Please add a commit to update the version in `{version_file}`'
                    ''.format(package=package, version_file=version_file)
                )


if __name__ == '__main__':
    main()
