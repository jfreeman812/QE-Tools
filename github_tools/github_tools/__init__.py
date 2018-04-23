#!/usr/bin/env python
import argparse
import collections
import datetime
import email.mime.multipart
import email.mime.text
import os
import re
import shutil
import smtplib
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import github3
import github3.users
import qecommon_tools
import requests


class UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return datetime.timedelta(0)


NOW = datetime.datetime.now(UTC())
PULL_WAIT = 20 * 60 * 60


def get_reviews(token, organization, pr_age, name_filter=''):
    reviews = collections.defaultdict(set)
    gh = github3.login(token=token, url='https://github.rackspace.com')
    org = gh.organization(organization)
    repos = set()
    for team in (x for x in org.iter_teams() if x.name.startswith(name_filter)):
        repos.update(team.iter_repos())
    for repo in repos:
        for pull in (x for x in repo.iter_pulls() if x.state == 'open'):
            assignees = {github3.users.User(x, pull) for x in pull._json_data.get('assignees')}
            if not assignees:
                continue
            secs_since_last_update = (NOW - pull.updated_at).total_seconds()
            # Check the assignee list and ensure it is not solely the author. In the case of
            # ambiguity, err on the side of caution and alert all parties involved.
            if {pull.user} != assignees and secs_since_last_update > pr_age:
                for assignee in assignees:
                    reviews[assignee].add((pull.title, pull.html_url))
    return reviews


def send_email(user, review_list):
    msg = email.mime.multipart.MIMEMultipart('alternative')
    msg['Subject'] = 'Pull Requests Needing Attention'
    msg['From'] = 'rs-pr-checker@rackspace.com'
    # Get Name and address from Hozer, since it's not in GitHub
    req = requests.get('https://finder.rackspace.net/mini.php?q={}'.format(user))
    for line in req.text.splitlines():
        match = re.match('^<tr><td>(?P<name>.*?)</td>.*<td>(?P<email>.*?)</td></tr>$', line)
        if match:
            to_address = match.groupdict()['email']
            msg['To'] = '{} <{}>'.format(*match.groups())
    text = 'The following Pull Requests need review:\n'
    html = '<html><body><p>The following Pull Requests need review:</p><ul>'
    for title, issue_url in review_list:
        text += '{} - {}\n'.format(title, issue_url)
        html += '<li><a href="{}">{}</a></li>'.format(issue_url, title)
    html += '</ul></body></html>'
    msg.attach(email.mime.text.MIMEText(text, 'plain'))
    msg.attach(email.mime.text.MIMEText(html, 'html'))

    s = smtplib.SMTP('smtp1.dfw1.corp.rackspace.com')
    s.sendmail(msg['From'], to_address, msg.as_string())
    s.quit()


def main(token, organization, name_filter, pr_age):
    for user, review_list in get_reviews(token, organization, pr_age,
                                         name_filter=name_filter).items():
        send_email(user, review_list)


def pr_checker():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name-filter', help='Filter for team names, if needed', default='')
    parser.add_argument('token', help='GitHub Token')
    parser.add_argument('organization', help='GitHub Organization')
    wait_help = 'Time, in seconds, to check the PR age against'
    parser.add_argument('--pr-age', default=PULL_WAIT, help=wait_help)
    args = parser.parse_args()
    main(args.token, args.organization, args.name_filter, args.pr_age)


def _update_hooks(update_dir, force, source_hooks):
    '''Find existing repositories and install hooks'''
    for dir_path, dir_names, file_names in os.walk(update_dir):
        if '.git' in dir_names:
            if force:
                existing_dir = os.path.join(dir_path, '.git', 'hooks')
                for existing_hook in source_hooks.intersection(os.listdir(existing_dir)):
                    os.remove(os.path.join(existing_dir, existing_hook))
            qecommon_tools.safe_run(['git', 'init'], cwd=dir_path)


def install_hooks():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Install helpful git hook templates')
    update_help = 'Optional list of directories to scan for git projects and update the hooks.'
    parser.add_argument('update_paths', nargs='*', help=update_help)
    parser.add_argument('--force', action='store_true',
                        help='Override git hooks in existing git projects')
    parser.add_argument('--template-path', default='~/.git-templates',
                        help='Path to install hook templates')
    args = parser.parse_args()
    # Update git config for template path
    config_command = ['git', 'config', '--global', 'init.templatedir', args.template_path]
    qecommon_tools.safe_run(config_command)
    # Create necessary directories
    destination_dir = os.path.expanduser(os.path.join(args.template_path, 'hooks'))
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    # Copy hooks to template directory
    source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hooks')
    source_hooks = set(os.listdir(source_dir))
    for source_hook in source_hooks:
        shutil.copy(os.path.join(source_dir, source_hook), destination_dir)
    # (Optionally) Update any git repositories found in the provided path(s)
    for update_dir in args.update_paths:
        _update_hooks(update_dir, args.force, source_hooks)


class GHPRSession(requests.Session):
    '''A GitHub session for managing a Pull Request.'''

    base_url = None

    def __init__(self, token, domain, repo, pull_id):
        super(GHPRSession, self).__init__()
        self.headers.update({'Authorization': 'token {}'.format(token)})
        self.base_url = self._base_url(domain, repo, pull_id)

    def _base_url(self, domain, repo, pull_id):
        # In repos without an active Issues section,
        # the Issue ID and PR ID *should* match,
        # but we will always positively grab the issue link from the PR
        # to prevent mis-commenting
        pull_data = self.get(
            'https://{}/api/v3/repos/{}/pulls/{}'.format(domain, repo, pull_id)
        ).json()
        # ensure a single trailing slash to support proper urljoin
        return pull_data.get('issue_url').rstrip('/') + '/'

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.base_url, url)
        response = super(GHPRSession, self).request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response

    def post_comment(self, comment_body):
        return self.post('comments', json={'body': comment_body})


class _GitHubPRBInfo(object):
    '''A class for getting GitHub Pull Request Builder related Jenkins env variables.'''

    @property
    def repository(self):
        return qecommon_tools.var_from_env('ghprbGhRepository')

    @property
    def pull_request_id(self):
        return qecommon_tools.var_from_env('ghprbPullId')

    @property
    def domain(self):
        return qecommon_tools.var_from_env('ghprbPullLink').strip('https://').split('/')[0]


ghprb_info = _GitHubPRBInfo()
'''_GitHubPRBInfo: An object that dynamically gets GHPRB Plugin related Jenkins env variables.'''


def get_github_commenter_parser(name='GitHub Pull Request Commenter'):
    parser = argparse.ArgumentParser(name)
    parser.add_argument('token', help='GitHub Personal Access Token for commenting user')
    return parser


if __name__ == '__main__':
    pr_checker()
