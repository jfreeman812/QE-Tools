'''
Some simple API functions and command-line tools for interacting with JIRA.


Setup
-----
All the tools and functions here need your specific information from
a ``jira.config`` file in your home directory, so you have to do this setup
before anything can be used:

* run ``jira-example-config --install`` to install an example config file
  (you can run it without ``--install`` to see the contents of what would be
  installed. (If you already have a ``jira.config`` in your home directory,
  this script will `not` overwrite it.)
* Fill out the values in the config file with your appropriate data
  (see the comments in that file for guidance).


Command-Line Tools
------------------

``jira-example-config`` can install an example config file for you, see above.

``jira-make-linked-issue`` makes a new JIRA issue that is linked to an exisiting issue;
the new issue's fields can be set from defaults in your ``jira.config``
or those values can be overridden on the command line.
See ``--help`` on this command for all the command line options,
and the comments in ``jira.config`` for setting the defaults.

``jira-add-comment`` adds a comment to a JIRA issue.
The ``jira.config`` file is needed to authenticate to JIRA.
No other data from the ``jira.config`` file is used by this commmand.
See ``--help`` on this command for details. You can also use ``-`` as your comment
and ``jira-add-comment`` will read the comment from stdin instead. Note that if you
use ``-`` interactively, you cannot edit your comment before it is posted.

.. note::
    ``qe_jira`` is deprecated, please use ``jira-make-linked-issue`` instead.
    ``qe_jira`` will be removed in a future release.

Examples
~~~~~~~~

* ``jira-add-comment JIRA-1234 "Work in Progress. PR delayed by network problems."``
  -- Add the comment to JIRA-1234 using the user/password from your ``jira.config``
  Note that the comment has to be just one command line argument surrounded by quotes
  if it contains spaces, etc.
* ``jira-make-linked-issue JIRA-1234``
  -- will create a JIRA in your ``TEST_PROJECT`` to test JIRA-1234,
  and link the two, assigning it to you and
  adding any watchers specified in your default watchers list.
* ``jira-make-linked-issue JIRA-1234 --project OTHER``
  -- will create a test JIRA as above, but in ``OTHER``
* ``jira-make-linked-issue JIRA-1234 --user bobm5523``
  -- will create the JIRA as above, but assign to ``bobm5523``
* ``jira-make-linked-issue JIRA-1234 -w sall9987 -w benj4444``
  -- will create the JIRA and assign ``sall9987`` and ``benj4444`` as watchers
  instead of your default watcher list

API Documentation
-----------------
'''

from __future__ import print_function
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter
from configparser import ConfigParser
import os
import shutil
import sys

from qecommon_tools import error_if
import jira


REQUIRED_KEYS = ('JIRA_URL', 'USERNAME', 'PASSWORD', 'DEFAULT_ASSIGNEE', 'TEST_PROJECT')


CONFIG_FILENAME = os.path.join(os.path.expanduser('~'), 'jira.config')
SAMPLE_CONFIG_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'jira.config.example')
CONFIG = None


def _load_config():
    '''Load CONFIG_FILENAME into CONFIG, if not already loaded; call before touching CONFIG'''
    global CONFIG
    if CONFIG is not None:
        return

    config = ConfigParser()
    message = 'Config file "{}" {{}}'.format(CONFIG_FILENAME)
    error_if(not os.path.exists(CONFIG_FILENAME), message=message.format('not found'))
    config.read(CONFIG_FILENAME)
    section_name = 'jira'
    error_if(section_name not in config,
             message=message.format('missing "{}" section'.format(section_name)))
    missing_keys = [key for key in REQUIRED_KEYS if key not in config[section_name]]
    missing_message = message.format('section "{}" missing keys: {{}}'.format(section_name))
    error_if(missing_keys, status=1, message=missing_message)
    CONFIG = config[section_name]


def get_client():
    '''Returns a JIRA client configured per the user's home directory ``jira.config`` file.'''
    _load_config()
    client = jira.JIRA(
        CONFIG['JIRA_URL'], basic_auth=(CONFIG['USERNAME'], CONFIG.get('PASSWORD', raw=True))
    )
    return client


def format_as_code_block(text_to_wrap):
    '''
    Wrap the text in a JIRA code block.

    Args:
        text_to_wrap (str): The text to wrap.

    Returns:
        str: A JIRA formatted code block.
    '''
    return ''.join(['{code:java}', '{}'.format(text_to_wrap), '{code}'])


def add_comment(jira_id, comment_text):
    '''
    Add a comment to the JIRA ID.

    Args:
        jira_id (str): The JIRA ID to comment on.
        comment_text (str): The text to add as the comment body.

    Returns:
        A jira comment.
    '''
    return get_client().add_comment(jira_id, comment_text)


def _link_jiras(client, from_jira, to_jira):
    return client.create_issue_link('relates to', from_jira, to_jira)


def _list_from_config(key_name):
    _load_config()
    return list(filter(None, [x.strip() for x in CONFIG.get(key_name, '').split(',')]))


def _component_id_from_name(project_components, component_name):
    matches = [x.id for x in project_components if x.name == component_name]
    message = 'More than one component in project with name: {}'
    error_if(len(matches) != 1, message=message.format(component_name))
    return matches[0]


def _get_args():
    _load_config()
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
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
                        default=_list_from_config('DEFAULT_COMPONENTS'),
                        action='append', help='Component tag to be aplied to the QE Story')
    parser.add_argument('-d', '--description', default=CONFIG['DEFAULT_DESCRIPTION'],
                        help='Description string for QE JIRA.')
    parser.add_argument('-l', '--labels', default=_list_from_config('DEFAULT_LABELS'),
                        action='append',
                        help='Comma-separated list of labels to be applied to the QE story')
    parser.add_argument('-s', '--summary', default=CONFIG['DEFAULT_SUMMARY'],
                        help='Summary string for QE JIRA - will receive the Dev JIRA key and '
                             'summary as string format values')
    parser.add_argument('-t', '--issue-type', default=CONFIG['DEFAULT_ISSUE_TYPE'],
                        help='Issue type for QE JIRA -- '
                             'must be a valid type name on target project')
    parser.add_argument('-w', '--watchers', action='append',
                        default=_list_from_config('WATCHERS'),
                        help='Watchers to add to QE JIRA')
    args = parser.parse_args()
    return args


def _cli_add_comment():
    '''
    Quick "add a short comment to a JIRA" command line tool.

    If 'message' is '-' then stdin will be read.
    '''
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description=_cli_add_comment.__doc__)
    parser.add_argument('jira_id')
    parser.add_argument('message', help='Comment to add to the given JIRA.')
    args = parser.parse_args()

    if args.message == '-':
        args.message = sys.stdin.read()
        print()

    print('Adding comment "{}" to "{}"'.format(args.message, args.jira_id))
    try:
        add_comment(args.jira_id, args.message)
    except jira.exceptions.JIRAError as e:
        print('ERROR: "{}" for "{}"!'.format(e.text, args.jira_id))


def _cli_search():
    '''
    Search using JQL and return matches.
    '''
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter, description=_cli_search.__doc__
    )
    parser.add_argument('--max-results', '-m', type=int, default=10)
    parser.add_argument('query')
    args = parser.parse_args()

    client = get_client()
    results = client.search_issues(args.query, maxResults=args.max_results)

    for issue in results:
        print('{}: {}'.format(issue.permalink(), issue.fields.summary))


def _create_qe_jira_from():
    args = _get_args()
    client = get_client()
    try:
        dev_jira = client.issue(args.jira_id)
    except jira.exceptions.JIRAError:
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
    _link_jiras(client, qe_jira.key, dev_jira.key)
    for to_watch in args.watchers:
        client.add_watcher(qe_jira.key, to_watch)
    print('QE JIRA Created: {}'.format(qe_jira.permalink()))


def _example_config_install():
    error_if(not os.path.exists(SAMPLE_CONFIG_FILENAME),
             message='Missing example config file: {}'.format(SAMPLE_CONFIG_FILENAME))

    parser = ArgumentParser(description='Install example jira.config in your homne directory '
                                        'unless you have one already. Without any command line '
                                        'switches, do a dry-run and print the example config file '
                                        'contents to stdout.')
    parser.add_argument('--install', action='store_true',
                        help='Install the example config file unless you have one already')
    args = parser.parse_args()

    prefix = 'Copying' if args.install else 'Would copy'
    print('{} {} to {}'.format(prefix, SAMPLE_CONFIG_FILENAME, CONFIG_FILENAME))
    if args.install:
        message = 'Not installing, config file already in place: {}'.format(CONFIG_FILENAME)
        error_if(os.path.exists(CONFIG_FILENAME), message=message)
        shutil.copy(SAMPLE_CONFIG_FILENAME, CONFIG_FILENAME)
    else:
        with open(SAMPLE_CONFIG_FILENAME) as input:
            shutil.copyfileobj(input, sys.stdout)
