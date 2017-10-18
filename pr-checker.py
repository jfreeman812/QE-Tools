#!/usr/bin/env python
'''
Overdue PR Checker

This PR checker is designed to signal a reviewer if a PR has not been reviewed within a given time
period. This checker works by getting the repositories associated with a provided organization and
(optionally) filtering by team name. This is done instead of providing a list of repositories to
the script because when repository is created and associated with a team, no changes would need to
be made to the arguments provided to this script.
'''

import argparse
import collections
import datetime
import email.mime.multipart
import email.mime.text
import re
import smtplib

import github3
import github3.users
import requests

NOW = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
PULL_WAIT = 20 * 60 * 60


def get_reviews(token, organization, pr_age, name_filter=''):
    reviews = collections.defaultdict(set)
    gh = github3.login(token=token, url='https://github.rackspace.com')
    org = gh.organization(organization)
    repos = set()
    for team in (x for x in org.iter_teams() if x.name.startswith('')):
        repos.update(team.iter_repos())
    for repo in repos:
        for pull in (x for x in repo.iter_pulls() if x.state == 'open'):
            assignees = {github3.users.User(x, pull) for x in pull._json_data.get('assignees')}
            if not assignees:
                continue
            secs_since_last_update = (NOW - pull.updated_at).total_seconds()
            if set([pull.user]) != assignees and secs_since_last_update > pr_age:
                for assignee in assignees:
                    reviews[assignee].add((pull.title, pull.html_url))
    return reviews


def send_email(user, review_list):
    msg = email.mime.multipart.MIMEMultipart('alternative')
    msg['Subject'] = 'Pull Requests Needing Attention'
    msg['From'] = 'pr-checker@rackspace.com'
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name-filter', help='Filter for team names, if needed')
    parser.add_argument('token', help='GitHub Token')
    parser.add_argument('organization', help='GitHub Organization')
    wait_help = 'Time, in seconds, to check the PR age against'
    parser.add_argument('pr_age', default=PULL_WAIT, help=wait_help)
    args = parser.parse_args()
    main(args.token, args.organization, args.name_filter, args.pr_age)
