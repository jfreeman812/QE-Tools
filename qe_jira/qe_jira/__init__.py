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


def _list_from_config(value):
    return [x.strip() for x in value.split(',')]


def _component_id_from_name(project_components, component_name):
    matches = [x.id for x in project_components if x.name == component_name]
    assert len(matches) == 1, 'More than one matching component!'
    return matches[0]


@click.command()
@click.argument('jira_id')
@click.option('--assign/--no-assign', default=bool(CONFIG['DEFAULT_ASSIGNEE']),
              help='Assign story to user or leave empty.')
@click.option('-p', '--project', default=CONFIG['TEST_PROJECT'],
              help='JIRA project in which to create test story')
@click.option('-u', '--user', default=CONFIG['DEFAULT_ASSIGNEE'],
              help='the user who will receive the assignment')
@click.option('-c', '--components', default=_list_from_config(CONFIG['DEFAULT_COMPONENTS']),
              multiple=True, help='Component tag to be aplied to the QE Story')
@click.option('-d', '--description', default=CONFIG['DEFAULT_DESCRIPTION'],
              help='Description string for QE JIRA.')
@click.option('-l', '--labels', default=_list_from_config(CONFIG['DEFAULT_LABELS']), multiple=True,
              help='Comma-separated list of labels to be applied to the QE story')
@click.option('-s', '--summary', default=CONFIG['DEFAULT_SUMMARY'],
              help='Summary string for QE JIRA - will receive the Dev JIRA key and summary '
                   'as string format values')
@click.option('-t', '--issue-type', default=CONFIG['DEFAULT_ISSUE_TYPE'],
              help='Issue type for QE JIRA -- must be a valid type name on target project')
@click.option('-w', '--watchers', multiple=True, default=_list_from_config(CONFIG['WATCHERS']),
              help='Watchers to add to QE JIRA')
def test_jira_from(jira_id, assign, project, user, components, description,
                   labels, summary, issue_type, watchers):
    client = get_client()
    try:
        dev_jira = client.issue(jira_id)
    except jira.exceptions.JIRAError as e:
        click.echo('JIRA {} was not found!'.format(jira_id))
        exit(1)
    issue_data = {
        'project': project,
        'summary': summary.format(dev_jira_id=dev_jira.key,
                                  dev_jira_summary=dev_jira.fields.summary),
        'description': description,
        'issuetype': {'name': issue_type},
    }
    if assign:
        issue_data.update(assignee={'name': user or client.current_user()})
    if labels:
        issue_data.update(labels=labels)
    if components:
        project_components = client.project_components(project)
        issue_data.update(components=[{'id': _component_id_from_name(project_components, x)}
                                      for x in components])
    qe_jira = client.create_issue(**issue_data)
    link_jiras(client, qe_jira.key, dev_jira.key)
    for to_watch in watchers:
        client.add_watcher(qe_jira.key, to_watch)
    click.echo('QE JIRA Created: {}'.format(qe_jira.permalink()))


if __name__ == '__main__':
    test_jira_from()
