import collections
import datetime
import email.mime.multipart
import email.mime.text
import re
import smtplib
import sys

import github3
import github3.users
import requests

NOW = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
PULL_WAIT = 20 * 60 * 60


def get_reviews(token):
    reviews = collections.defaultdict(set)
    gh = github3.login(token=token, url='https://github.rackspace.com')
    org = gh.organization('AutomationServices')
    repos = set()
    for team in (x for x in org.iter_teams() if x.name.startswith('rba-qe')):
        repos.update(team.iter_repos())
    for repo in repos:
        for pull in (x for x in repo.iter_pulls() if x.state == 'open'):
            assignees = [github3.users.User(x, pull) for x in pull._json_data.get('assignees')]
            if not assignees:
                continue
            last_update = (NOW - pull.updated_at).total_seconds()
            if pull.user not in assignees and last_update > PULL_WAIT:
                for assignee in assignees:
                    reviews[assignee].add((pull.title, pull.issue_url))
    return reviews


def send_email(user, review_list):
    msg = email.mime.multipart.MIMEMultipart('alternative')
    msg['Subject'] = 'Pull Requests Needing Attention'
    msg['From'] = 'rba-qe@rackspace.com'
    # Get Name and address from Hozer, since its not in GitHub
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
    part_one = email.mime.text.MIMEText(text, 'plain')
    part_two = email.mime.text.MIMEText(html, 'html')
    msg.attach(part_one)
    msg.attach(part_two)

    s = smtplib.SMTP('smtp1.dfw1.corp.rackspace.com')
    s.sendmail(msg['From'], to_address, msg.as_string())
    s.quit()


def main(token):
    for user, review_list in get_reviews(token).items():
        send_email(user, review_list)


if __name__ == '__main__':
    main(sys.argv[1])
