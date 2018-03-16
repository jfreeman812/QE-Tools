#!/usr/bin/env python3 # noqa
'''Tool that runs a specified Jenkins job with configurable parameters.'''

import json
import argparse
import sys
import re
import time
import urllib.parse
import urllib.error
import urllib.request
import configparser
from http import HTTPStatus


# Verifies that a string is a URL. Taken from the source code of the Python Django framework
URL_REGEX = re.compile(
    r'^(?:http)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain..
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

SECTION_BREAK = '\n{0}\n'.format('#' * 70)

# Variables updated from config file
JENKINS_URL = ''
JENKINS_TOKEN = ''
TIMEOUT = None  # in seconds

# Used when printing job output
MAX_RETRY_COUNT = 3
RETRY_SLEEP_SECS = 5


def make_http_request(http_url, url_endpoint='', request_params=None):
    '''Make an HTTP request to the specified URL with the parameters.

    Args:
        http_url (str): A str containing the URL of the HTTP request
        url_endpoint (Union[str, int]): An endpoint to add at the end of the URL. (optional)
        request_params (dict): The HTTP request parameters. (optional)

    Returns:
        Tuple[int, str]: The HTTP response code and HTTP response body
    '''
    if url_endpoint == 'buildWithParameters' or url_endpoint == 'build':
        request_params = {
            'token': JENKINS_TOKEN,
            'json': request_params
        }

    if isinstance(url_endpoint, int):
        http_url = http_url + str(url_endpoint) + '/api/json'
    else:
        http_url = http_url + url_endpoint

    if request_params is not None:
        request_params = bytes(urllib.parse.urlencode(request_params).encode('utf8'))

    try:
        response = urllib.request.urlopen(http_url, request_params, timeout=TIMEOUT)
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode('utf8')
    except Exception as e:
        eprint('Failed to make an HTTP connection.')
        eprint(e)
        sys.exit(1)
    else:
        code = response.code
        body = response.read().decode('utf8')
        response.close()
    finally:
        return code, body


def _get_choice_selection(start, end, selection_list, statement, default=None):
    '''Get the choice selection from the user and ensure it is valid.

    If the user does not pick a selection, then use the default value if it is set,
    else prompt the user again.

    Args:
        start (int): The lowest valid selection from the multiple choices
        end (int): The highest valid selection from the multiple choices
        selection_list (list): The list containing the valid selections
        statement (str): The text to show the user when asking for an input
        default (int): The default choice (optional)

    Returns:
        Any: The user selection if it is valid
    '''
    selection = input('\n{0}'.format(statement))
    while not (selection.isdigit() and start <= int(selection) <= end):
        if selection == '' and default is not None:
            return default
        selection = input('Invalid selection. {0}'.format(statement))
    return selection_list[int(selection) - 1]


def _get_input_selection(param_name, validation_function=None, default=''):
    '''Get the input selection from the user and ensure it is valid.

    If the user does not type in a value, then use the default value if it is set,
    else prompt the user again.

    Args:
        param_name (str): The name of the parameter
        validation_function (function): A function to use to validate the user input (optional)
        default (str): The default parameter value (optional)

    Returns:
        str: The user input if it is valid
    '''
    statement = 'Please enter a value for the parameter "{0}"'.format(param_name)
    if default:
        statement += ' [{0}]'.format(default)
    statement += ': '

    input_value = input(statement) or default

    while input_value == '' or \
            validation_function is not None and not validation_function(input_value):
        input_value = input('Invalid value. {0}'.format(statement)) or default

    return input_value


def _get_default_value(param):
    '''Return the default parameter value, if one exists, else return an empty string.

    Args:
        param (dict): The parameter to get the default value for

    Returns:
        str: The default value for the parameter
    '''
    if 'defaultParameterValue' in param:
        return param['defaultParameterValue']['value']
    return ''


def interactive_mode():
    '''Run the interactive mode by prompting the user for each input and validating it.'''
    state = 'JOB_SELECTION'
    quick_command = [sys.argv[0]]

    http_code, http_body = make_http_request('{0}/api/json'.format(JENKINS_URL))
    if http_code != HTTPStatus.OK:
        eprint('Cannot get list of jobs from Jenkins: HTTP {0}:\n{1}'.format(http_code, http_body))
        sys.exit(1)

    list_of_jobs = json.loads(http_body)['jobs']
    options_reg = re.compile('(?<=Options are: )([^, ]+)[, ]?(?=\\n)')

    # Begin interactive mode
    while True:
        # Ask what Jenkins job to run
        if state == 'JOB_SELECTION':
            print('\nThe following Jenkins jobs were found:')
            for num, job in enumerate(list_of_jobs, start=1):
                print('{0}. {1}'.format(num, job['name']))

            message = ('Please select a number for the Jenkins jobs to execute (1-{0}): '
                       ''.format(len(list_of_jobs)))
            selected_job = _get_choice_selection(start=1, end=len(list_of_jobs),
                                                 selection_list=list_of_jobs, statement=message)

            quick_command.extend(('--job', selected_job['name']))
            state = 'PARAMETER_SELECTION'
            print('')

        # Ask for all of the job parameters
        elif state == 'PARAMETER_SELECTION':
            selected_job_params = {}
            http_code, http_body = make_http_request(selected_job['url'], 'api/json')
            if http_code != HTTPStatus.OK:
                eprint('Error retrieving a list of parameters for the job: HTTP {0}:\n{1}'
                       ''.format(http_code, http_body))
                sys.exit(1)
            try:
                job_params = json.loads(http_body)['actions'][0]['parameterDefinitions']
            except KeyError:
                # Job has no parameters. Go to state 'DISPLAY_RESULTS' and build the job
                state = 'DISPLAY_RESULTS'
                continue
            for param in job_params:
                # Parameters with options
                if 'Options are:' in param['description']:
                    print('Choices for parameter "{0}":'.format(param['name']))
                    options = options_reg.findall(param['description'])
                    default = _get_default_value(param)
                    for count, option in enumerate(options, start=1):
                        print('{0}. {1}'.format(count, option))
                        if option == default:
                            default_index = count

                    statement = ('Please select one of the options above [{0}. {1}]: '
                                 ''.format(default_index, default))
                    selected_job_params[param['name']] = \
                        _get_choice_selection(start=1, end=len(options), selection_list=options,
                                              default=default_index, statement=statement)

                    quick_command.extend(('--{0}'.format(param['name']),
                                         selected_job_params[param['name']]))

                # Parameters with no options
                else:
                    default = _get_default_value(param)

                    validation_function = None
                    if param['name'] == 'url':
                        validation_function = URL_REGEX.match
                    value_input = _get_input_selection(param['name'], validation_function, default)

                    selected_job_params[param['name']] = value_input
                    quick_command.extend(('--{0}'.format(param['name']), value_input))
                print('')
            state = 'DISPLAY_RESULTS'

        # Make the HTTP requests to run the job then display the result when it is finished running
        elif state == 'DISPLAY_RESULTS':
            run_job_and_display_result(selected_job, selected_job_params)

            print(SECTION_BREAK)
            print('A quick command to run this job with the selected parameters:')
            print(' '.join(quick_command))
            return


def run_job_and_display_result(job, job_params):
    '''Run the specified Jenkins job and display the results of said job once it finishes.

    Args:
        job (dict): The Jenkins job to run with its Jenkins URL
        job_params (dict): The job parameters and the values chosen for each
    '''
    # First we find the build number of the last job's build to use it for polling
    last_job_build_number = _get_last_job_build_number(job['url'])

    # Next we build the job
    url_endpoint = 'buildWithParameters' if job_params else 'build'
    http_code, http_body = make_http_request(job['url'], url_endpoint, job_params)
    if http_code != HTTPStatus.CREATED:
        eprint('Error building the the Jenkins job: HTTP {0}:\n{1}'.format(http_code, http_body))
        sys.exit(1)
    print('Began executing Jenkins job')

    # Poll to check the build status of the job
    # When the job is finished, a field with the name 'result' will show a value such as
    # 'SUCCESS' or 'FAILURE'
    new_job_build_number = last_job_build_number + 1
    job_in_queue = _job_in_queue(job['name'], job_params, check_delay=10)
    while True:
        http_code, http_body = make_http_request(job['url'], new_job_build_number)
        # The new job ID has not been assigned yet. Jenkins nodes are most likely all busy
        if http_code == HTTPStatus.NOT_FOUND:
            if not job_in_queue:
                eprint('The job does not seem to be in the Jenkins queue, '
                       'nor is it being run by Jenkins.')
                eprint(http_body)
                sys.exit(1)
            job_in_queue = _job_in_queue(job['name'], job_params, check_delay=1)
            continue
        http_body = json.loads(http_body)
        if not (job_params and not _job_has_correct_parameters(http_body, job_params)):
            break
        new_job_build_number += 1
        time.sleep(5)

    # Display the console output of the Jenkins job
    _print_job_output_intermittently(job, new_job_build_number)


def _print_job_output_intermittently(job, job_build_number):
    '''Print the job's output intermittently.

    Args:
        job (dict): The dict containing the job's name and URL
        job_build_number (int): The build number of the job to print the results of
    '''
    start = 0
    job_is_done = False
    http_fail_count = 0
    job_finish_regex = re.compile('Finished: (SUCCESS|FAILURE|ABORTED)$')
    # Used to add a clickable URL to the log file of the job run
    log_files_regex = re.compile('(Detailed logs: /var/lib/jenkins/workspace/{0})(/logs/[0-9-_.]+)'
                                 ''.format(job['name']))

    print(SECTION_BREAK)
    print('Output of Jenkins job "{0}"\n'.format(job['name']))

    while not job_is_done:
        if http_fail_count == MAX_RETRY_COUNT:
            eprint('The tool is having trouble connecting to Jenkins. '
                   'Please ensure that Jenkins is still up.')
            sys.exit(1)

        http_code, http_body = make_http_request(job['url'],
                                                 '{0}/consoleText'.format(job_build_number))
        if http_code != HTTPStatus.OK:
            http_fail_count += 1
            time.sleep(RETRY_SLEEP_SECS)
            continue
        else:
            http_fail_count = 0

        if job_finish_regex.search(http_body[start:]):
            job_is_done = True
        if log_files_regex.search(http_body[start:]):
            http_body = log_files_regex.sub('Detailed logs: {0}ws\g<2>/cafe.master.log'
                                            ''.format(job['url']), http_body)

        print(http_body[start:], end='')
        start = len(http_body)
        time.sleep(1)


def _get_last_job_build_number(job_url):
    '''Return the build number of the last job build.

    Args:
        job_url (str): The job's URL

    Returns:
        int: The build number of the last job build
    '''
    http_code, http_body = make_http_request(job_url, 'lastBuild/buildNumber')
    if http_code == HTTPStatus.OK:
        return int(http_body)
    elif http_code == HTTPStatus.NOT_FOUND:
        # job was never run before
        return 0
    else:
        eprint('Error retrieving last build ID before running the job: HTTP {0}:\n{1}'
               ''.format(http_code, http_body))
        sys.exit(1)


def _job_in_queue(job_name, job_params, check_delay=10):
    '''Verify that a certain Jenkins job is in the Jenkins job queue.

    Args:
        job_name (str): The name of the job to check in the Jenkins queue
        job_params (dict): A dict containing the job's parameters
        check_delay (int): The amount of seconds to wait before checking the queue. Defaults to 10

    Returns:
        bool: Whether the job is in the queue
    '''
    time.sleep(check_delay)
    queue_url = '{0}/queue/api/json'.format(JENKINS_URL)
    http_code, http_body = make_http_request(queue_url)
    if http_code != HTTPStatus.OK:
        return False
    http_body = json.loads(http_body)
    for job in http_body['items']:
        if job_name == job['task']['name'] and job_params and \
                _job_has_correct_parameters(http_body['items'][0], job_params):
            return True
    return False


def _job_has_correct_parameters(http_body, job_params):
    '''Verify that the job parameters and their values match the selected ones.

    This is a rare scenario, but needed to be addressed. An example would be as such:
        - User 1 uses this tool to run a job with specific parameters.
        - One or more users run the same job at the same time from the Jenkins web UI,
          some with different parameters.

    In the scenario above, this would ensure that the results retrieved from Jenkins match
    the same parameters selected by User 1. This would avoid any confusions that may come up.

    Args:
        http_body (dict): The JSON response from an HTTP GET call
        job_params (dict): A dict keyed by the name of the parameter values being parameter values

    Returns:
        bool: True if the parameter names and values match, else False
    '''
    if len(job_params) != len(http_body['actions'][0]['parameters']):
        return False
    for param in http_body['actions'][0]['parameters']:
        if param['name'] not in job_params or param['value'] != job_params[param['name']]:
            return False
    return True


def _is_account_device(account_device):
    '''Verify that the input account:device pair is following the correct syntax.

    Args:
        account_device (str): The account:device pair to verify

    Returns:
        str: The account_device input if it is valid

    Raises:
        argparse.ArgumentTypeError: If the account_device input is invalid
    '''
    values = str(account_device).split(':')
    if len(values) == 2 and all(map(str.isdigit, values)):
        return account_device
    raise argparse.ArgumentTypeError('"{0}" is not a valid account:device ID pair '
                                     '(e.g. 990036:534583)'.format(account_device))


def _is_url(url):
    '''Verify that the input URL is a valid URL.

    Args:
        url (str): The base API URL to verify

    Returns:
        str: The URL input if it is valid

    Raises:
        argparse.ArgumentTypeError: If the URL input is invalid
    '''
    if not URL_REGEX.match(url):
        raise argparse.ArgumentTypeError('"{0}" is not a valid URL'.format(url))
    return str(url)


def eprint(*args, **kwargs):
    '''A print function that prints to stderr instead of stdout.'''
    print(*args, file=sys.stderr, **kwargs)


def read_config_and_set_globals(config_file):
    '''Read a config file and set the Jenkins global variables based on the file values.

    The config contains the base Jenkins URL, as well as a token that is used to access
    all of the jobs on that Jenkins server.
    '''
    global JENKINS_URL, JENKINS_TOKEN, TIMEOUT

    config = configparser.ConfigParser()

    try:
        config.read(config_file)

        JENKINS_TOKEN = config['jenkins']['token']

        if not URL_REGEX.match(config['jenkins']['url']):
            raise ValueError('Jenkins URL from config file is not a valid URL.')
        JENKINS_URL = config['jenkins']['url']

        if not config['jenkins']['url_timeout'].isdigit():
            raise ValueError('"url_timeout" value must be an int. Received value of {0} instead.'
                             ''.format(config['jenkins']['url_timeout']))
        TIMEOUT = int(config['jenkins']['url_timeout'])

    except configparser.Error as e:
        eprint('Error while attempting to read config file "{0}": {1}'.format(config_file, str(e)))
        sys.exit(1)
    except KeyError as e:
        eprint('Section or Key {0} is missing from "{1}" config file. File should have the '
               'following structure:\n{2}'.format(str(e), config_file, ('[jenkins]\n'
                                                                        'url=<jenkins_url>\n'
                                                                        'token=<token>\n'
                                                                        'url_timeout=<timeout>\n')))
        sys.exit(1)
    except ValueError as e:
        eprint(str(e))
        sys.exit(1)

    # In case the '/' was added at the end of the URL, ignore it
    JENKINS_URL = JENKINS_URL.rstrip('/')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='runjob')
    parser.add_argument('--config', type=str, default='config.cfg',
                        help='The name of the config file')
    args, unknown_args = parser.parse_known_args()
    read_config_and_set_globals(args.config)

    if not unknown_args:
        interactive_mode()
    else:
        parser.add_argument('--job', required=True, type=str,
                            help='The name of the Jenkins job to run')
        args = parser.parse_known_args()[0]

        job = {
            'name': args.job,
            'url': '{0}/job/{1}/'.format(JENKINS_URL, args.job)
        }
        http_code, http_body = make_http_request(job['url'], 'api/json')
        if http_code != HTTPStatus.OK:
            eprint('Error retrieving a list of parameters for the job "{0}"'.format(job['name']))
            sys.exit(1)

        try:
            job_params = json.loads(http_body)['actions'][0]['parameterDefinitions']
        except (KeyError, IndexError):
            job_params = {}
        else:
            for param in job_params:
                param_type = {'url': _is_url,
                              'account_device': _is_account_device}.get(param['name'], str)

                parser.add_argument('--{0}'.format(param['name']),
                                    default=param['defaultParameterValue']['value'],
                                    help=param['description'],
                                    type=param_type)

            args = parser.parse_args()

            job_params = {arg: args.__dict__[arg] for arg in args.__dict__
                          if arg not in ('job', 'config')}
        finally:
            run_job_and_display_result(job, job_params)
