from __future__ import print_function
from argparse import ArgumentParser
from configparser import ConfigParser
import os

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


def _list_from_config(key_name):
    return list(filter(None, [x.strip() for x in CONFIG.get(key_name, '').split(',')]))


def _component_id_from_name(project_components, component_name):
    matches = [x.id for x in project_components if x.name == component_name]
    message = 'More than one component in project with name: {}'
    assert len(matches) == 1, message.format(component_name)
    return matches[0]


def _get_args():
    parser = ArgumentParser()
    parser.add_argument('jira_id')
    parser.set_defaults(assign=bool(CONFIG['DEFAULT_ASSIGNEE']))
    assignment = parser.add_mutually_exclusive_group()
    assignment.add_argument('--assign', dest='assign', action='store_true',
                            help='Assign story to user, current user if none provided.')
    assignment.add_argument('--no-assign', dest='assign', action='store_false',
                            help='Leave QE JIRA unassigned')
    parser.add_argument('-p', '--project', default=CONFIG['TEST_PROJECT'],
                        help='JIRA project in which to create test story')
    parser.add_argument('-u', '--user', default=CONFIG['DEFAULT_ASSIGNEE'],
                        help='the user who will receive the assignment')
    parser.add_argument('-c', '--components',
                        default=_list_from_config(CONFIG['DEFAULT_COMPONENTS']),
                        action='append', help='Component tag to be aplied to the QE Story')
    parser.add_argument('-d', '--description', default=CONFIG['DEFAULT_DESCRIPTION'],
                        help='Description string for QE JIRA.')
    parser.add_argument('-l', '--labels', default=_list_from_config(CONFIG['DEFAULT_LABELS']),
                        action='append',
                        help='Comma-separated list of labels to be applied to the QE story')
    parser.add_argument('-s', '--summary', default=CONFIG['DEFAULT_SUMMARY'],
                        help='Summary string for QE JIRA - will receive the Dev JIRA key and '
                             'summary as string format values')
    parser.add_argument('-t', '--issue-type', default=CONFIG['DEFAULT_ISSUE_TYPE'],
                        help='Issue type for QE JIRA -- '
                             'must be a valid type name on target project')
    parser.add_argument('-w', '--watchers', action='append',
                        default=_list_from_config(CONFIG['WATCHERS']),
                        help='Watchers to add to QE JIRA')
    args = parser.parse_args()
    return args


def create_qe_jira_from():
    args = _get_args()
    client = get_client()
    try:
        dev_jira = client.issue(args.jira_id)
    except jira.exceptions.JIRAError as e:
        print('JIRA {} was not found!'.format(args.jira_id))
        exit(1)
    issue_data = {
        'project': args.project,
        'summary': args.summary.format(dev_jira_id=dev_jira.key,
                                       dev_jira_summary=dev_jira.fields.summary),
        'description': args.description,
        'issuetype': {'name': args.issue_type},
    }
    if args.assign:
        issue_data.update(assignee={'name': args.user or client.current_user()})
    if args.labels:
        issue_data.update(labels=args.labels)
    if args.components:
        project_components = client.project_components(args.project)
        issue_data.update(components=[{'id': _component_id_from_name(project_components, x)}
                                      for x in args.components])
    qe_jira = client.create_issue(**issue_data)
    link_jiras(client, qe_jira.key, dev_jira.key)
    for to_watch in args.watchers:
        client.add_watcher(qe_jira.key, to_watch)
    print('QE JIRA Created: {}'.format(qe_jira.permalink()))


if __name__ == '__main__':
    create_qe_jira_from()
