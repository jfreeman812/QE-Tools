#! /usr/bin/env python

from github_tools import GHPRSession, ghprb_info, get_github_commenter_parser
from qecommon_tools import get_file_docstring


def main():
    parser = get_github_commenter_parser('Docs link PR Commenter')
    parser.add_argument('sensitive_files', nargs='+', help='The sensitive files to check.')
    args = parser.parse_args()
    repo = ghprb_info.repository
    pull_id = ghprb_info.pull_request_id
    domain = ghprb_info.domain

    gh = GHPRSession(args.token, domain, repo, pull_id)

    for sensitive_file in args.sensitive_files:
        diff = gh.get_diff(files=sensitive_file)
        if diff:
            module_docstring = get_file_docstring(sensitive_file)
            gh.post_comment(
                '### Warning\n'
                '\n'
                'You\'ve changed a sensitive file! Make sure you understand the ramifications!\n'
                '\n'
                '**File Changed**: `{file_changed}`'
                '\n'
                '```\n'
                '{module_docstring}\n'
                '```'
                ''.format(file_changed=sensitive_file, module_docstring=module_docstring)
            )


if __name__ == '__main__':
    main()
