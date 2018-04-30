#! /usr/bin/env python

from github_tools import GHPRSession, ghprb_info, get_github_commenter_parser


SCHEMA_MODULE_NAME = 'data_broker/__schema_version__.py'


def main():
    parser = get_github_commenter_parser('Docs link PR Commenter')
    args = parser.parse_args()
    repo = ghprb_info.repository
    pull_id = ghprb_info.pull_request_id
    domain = ghprb_info.domain

    gh = GHPRSession(args.token, domain, repo, pull_id)
    diff = gh.get_diff(files=SCHEMA_MODULE_NAME)

    if diff:
        gh.post_comment(
            '### Warning\n'
            '\n'
            'Changing the DataBroker schema name in `{}` also requires a corresponding change '
            'to the Splunk dashboard that handles the data sent from the Data Broker. Do not '
            'change this value unless you simultaneously coordinate the additional changes '
            'needed in the Splunk dashboard.'.format(SCHEMA_MODULE_NAME)
        )


if __name__ == '__main__':
    main()
