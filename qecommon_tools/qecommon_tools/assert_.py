'''Convenience functions for doing asserts with helpful names and helpful messages.'''


try:
    from math import isclose as _isclose
except ImportError:
    # From: https://stackoverflow.com/questions/5595425/
    #        what-is-the-best-way-to-compare-floats-for-almost-equality-in-python/5595453
    def _isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def _msg_concat(prefix, body):
    '''Join with a space if prefix isn't empty'''
    return '{} {}'.format(prefix, body) if prefix else body


def not_eq(self, expected, actual, msg=''):
    assert expected != actual, _msg_concat(
        msg, "Expected '{}' to be not equal to actual '{}'".format(expected, actual))


def eq(self, expected, actual, msg=''):
    assert expected == actual, _msg_concat(
        msg, "Expected '{}' == actual '{}'".format(expected, actual))


def less(self, a, b, msg=''):
    assert a < b, _msg_concat(msg, "Expected '{}' < '{}'".format(a, b))


def less_equal(self, a, b, msg=''):
    assert a <= b, _msg_concat(msg, "Expected '{}' <= '{}'".format(a, b))


def is_in(self, value, sequence, msg=''):
    assert value in sequence, _msg_concat(
        msg, "Expected: '{}' to be in '{}'".format(value, sequence))


def any_in(self, a_sequence, b_sequence, msg=''):
    '''Assert at least one member of a_sequence is in b_sequence'''
    assert any(a in b_sequence for a in a_sequence), _msg_concat(
        msg, "None of: '{}' found in '{}'".format(a_sequence, b_sequence))


def not_in(self, item, sequence, msg=''):
    assert item not in sequence, _msg_concat(
        msg, "did not expected Element: '{}' to be in '{}'".format(item, sequence))


def is_true(self, a, msg=''):
    assert bool(a) is True, msg


def is_false(self, a, msg=''):
    assert bool(a) is False, msg


def is_not_none(self, a, msg=''):
    assert a is not None, _msg_concat(msg, "'{}' should not be None".format(a))


def is_not_empty(self, sequence, msg=''):
    '''
    Semantically more helpful than just ``assert sequence``.

    Sequences and containers in python are False when empty, and True when not empty.
    This helper reads better in the test code and in the error message.
    '''
    assert sequence, _msg_concat(msg, "'{}' - should not be empty".format(sequence))


def almost_equal(self, actual, expected, places=2, msg=''):
    # Set relative tolerance to 0 because we don't want that messing up the places check.
    relative_tolerance = 0
    absolute_tolerance = 10.0**(-places)
    assert _isclose(expected, actual,
                    rel_tol=relative_tolerance, abs_tol=absolute_tolerance), _msg_concat(
        msg, "Expected '{}' to be almost equal to '{}'".format(actual, expected))


def is_singleton_list(self, sequence, item_description='something', msg=''):
    '''Make sure the sequence has exactly one item (of item_description)'''
    assert len(sequence) == 1, _msg_concat(
        msg, "Expected to find a one item list of {} but found '{}' instead".format(
            item_description, sequence))


def is_instance(value, of_type, msg=''):
    assert isinstance(value, of_type), _msg_concat(
        msg, "Got value '{}' of type '{}' when expecting something of type {}".format(
            value, type(value), of_type))
