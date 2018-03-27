#! /usr/bin/env python

import argparse
import os
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests

DOC_PATH = 'HTML_Report'


class GHSession(requests.Session):
    base_url = None

    def __init__(self, token, domain, repo, pull_id):
        super(GHSession, self).__init__()
        self.headers.update({'Authorization': 'token {}'.format(token)})
        self.base_url = self._base_url(domain, repo, pull_id)

    def _base_url(self, domain, repo, pull_id):
        # In repos without an active Issues section,
        # the Issue ID and PR ID *should* match,
        # but we will always positively grab the issue link from the PR
        # to prevent mis-commenting
        url_template = 'https://{}/api/v3/repos/{}/{}/{}'
        pull_url = url_template.format(domain, repo, 'pulls', pull_id)
        pull_data = self.get(pull_url).json()
        return pull_data.get('issue_url') + '/'

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.base_url, url)
        response = super(GHSession, self).request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response

    def post_comment(self, comment_body):
        return self.post('comments', json={'body': comment_body})


def var_from_env(var_name):
    envvar = os.environ.get(var_name)
    if not envvar:
        raise ValueError('"{}" variable not found!'.format(var_name))
    return envvar


def main():
    parser = argparse.ArgumentParser('Docs link PR Commenter')
    parser.add_argument('token', help='GitHub Personal Access Token for commenting user')
    args = parser.parse_args()
    report_url = var_from_env('BUILD_URL') + '{}/'.format(DOC_PATH)
    repo = var_from_env('ghprbGhRepository')
    pull_id = var_from_env('ghprbPullId')
    domain = var_from_env('ghprbPullLink').strip('https://').split('/')[0]
    gh = GHSession(args.token, domain, repo, pull_id)
    gh.post_comment('Docs Link: {}'.format(report_url))


if __name__ == '__main__':
    main()
