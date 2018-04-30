#! /usr/bin/env python

from github_tools import GHPRSession, ghprb_info, get_github_commenter_parser
from qecommon_tools import var_from_env


DOC_PATH = 'HTML_Report'


def main():
    parser = get_github_commenter_parser('Docs link PR Commenter')
    args = parser.parse_args()

    repo = ghprb_info.repository
    pull_id = ghprb_info.pull_request_id
    domain = ghprb_info.domain
    gh = GHPRSession(args.token, domain, repo, pull_id)

    report_url = var_from_env('BUILD_URL') + '{}/'.format(DOC_PATH)
    gh.post_comment('Docs Link: {}'.format(report_url))


if __name__ == '__main__':
    main()
