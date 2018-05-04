import os
import logging
from tempfile import mkdtemp

import pytest
from qe_logging import behave_logging, setup_logging


LOG_FILENAME_PREFIX = 'qe_behave_logging_test'
BEHAVE_LOGGING_ATTRIBUTE = 'qe_behave_logging_filenames'


# Python2 doesn't have SimpleNamespace :-(
class Mock(object):
    pass


def teardown_function():
    # Handlers must be cleared or they will cause interference with other tests.
    del logging.getLogger('').handlers[:]


def _get_file_contents(*paths):
    with open(os.path.join(os.path.join(*paths)), 'r') as f:
        return f.read()


# before_all has different side-effects than the other behave before/after functions
# as such it has to be tested separately from them.
def test_behave_before_all():
    logging.getLogger().setLevel(logging.DEBUG)

    log_dir = mkdtemp()

    mock_context = Mock()
    mock_context.config = Mock()
    mock_context.config.setup_logging = lambda *args, **kwargs: None

    behave_logging.before_all(mock_context, LOG_FILENAME_PREFIX, base_log_dir=log_dir)

    # Note: there are other tests that validate setup_logging return values,
    # and other side-effects, etc.
    # All we have to validate here is that the context field is being set.

    attr_assert_msg = 'before_all failed to set {} attribute on context'.format(
        BEHAVE_LOGGING_ATTRIBUTE)
    assert hasattr(mock_context, BEHAVE_LOGGING_ATTRIBUTE), attr_assert_msg


@pytest.mark.parametrize(
    'method', [behave_logging.before_feature,
               behave_logging.before_scenario,
               behave_logging.before_step,
               behave_logging.after_feature,
               behave_logging.after_scenario,
               behave_logging.after_step,
               behave_logging.after_all
               ]
)
def test_log_files_contain_data(method):
    logging.getLogger().setLevel(logging.DEBUG)

    log_dir = mkdtemp()
    log_filenames = setup_logging(LOG_FILENAME_PREFIX, base_log_dir=log_dir)

    method_name = method.__name__

    mock_context = Mock()
    mock_context.config = Mock()
    mock_context.config.setup_logging = lambda *args, **kwargs: None

    mock_misc = Mock()  # Feature, step, etc.
    mock_misc.keyword = 'fake_keyword'
    mock_misc.name = method_name
    mock_misc.status = 'fake_status'

    if method_name == 'after_all':
        method(mock_context)
    else:
        method(mock_context, mock_misc)

    log_filename = log_filenames[0]  # Arbitrary choice.

    file_contents = _get_file_contents(log_filename)
    msg = '{} not found in log file, actual contents {}'.format(method_name, file_contents)
    assert 'behave.' in file_contents, msg
