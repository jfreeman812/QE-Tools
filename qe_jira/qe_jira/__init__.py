from configparser import ConfigParser
import os

import click
import jira


def get_configs():
    config = ConfigParser()
    config.read(os.path.join(os.path.expanduser('~'), 'jira.config'))
    return config['jira']


CONFIG = get_configs()


def get_client():
    client = jira.JIRA(CONFIG['JIRA_URL'], basic_auth=(CONFIG['USERNAME'], CONFIG['PASSWORD']))
    return client


def link_jiras(client, from_jira, to_jira):
    return client.create_issue_link('relates to', from_jira, to_jira)


@click.command()
@click.argument('jira_id')
@click.option('-p', '--project', default=CONFIG['TEST_PROJECT'],
              help='JIRA project in which to create test story')
@click.option('-u', '--user', default=None, help='the user who will receive the assignment')
@click.option('-w', '--watcher', multiple=True)
def test_jira_from(jira_id, project, user, watcher):
    client = get_client()
    try:
        dev_jira = client.issue(jira_id)
    except jira.exceptions.JIRAError as e:
        click.echo('JIRA {} was not found!'.format(jira_id))
        exit(1)
    click.echo('Found DEV Jira: {}'.format(dev_jira.permalink()))
    qe_jira = client.create_issue(
        project=project,
        summary='QE Testing for: {} - {}'.format(dev_jira.key, dev_jira.fields.summary),
        description='Do necessary QE testing around the linked Dev JIRA',
        issuetype={'name': 'Story'},
        assignee={'name': user or client.current_user()},
    )
    click.echo('Created {}'.format(qe_jira.permalink()))
    link_jiras(client, qe_jira.key, dev_jira.key)
    click.echo('Linked {} to {}'.format(qe_jira.permalink(), dev_jira.permalink()))
    watchers = watcher or CONFIG['WATCHERS'].split(',')
    for to_watch in watchers:
        client.add_watcher(qe_jira.key, to_watch)
        click.echo('Added watcher: {}'.format(to_watch))
    click.echo('Done!')


if __name__ == '__main__':
    test_jira_from()
