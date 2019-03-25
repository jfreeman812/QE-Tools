'''Unit Tests for the TableRead SimpleRSTReader.'''

import os
import tempfile

import pytest
import attr

import tableread


SAMPLE_TABLES = '''
Sample RST Table
================

First Table
-----------

====  ==============  ===============
Name  Favorite Color  Favorite Number
====  ==============  ===============
Bob   Red             3
Sue   Blue            5
Jim   Green           8
====  ==============  ===============

Second Table
------------

=======  ==============  =========
Planet   Order From Sun  Is Planet
=======  ==============  =========
Mercury  0               Yes
Venus    1               Yes
Earth    2               Yes
Mars     3               Yes
Jupiter  4               Yes
Saturn   5               Yes
Uranus   6               Yes
Neptune  7               Yes
Pluto    8               Forever Yes
=======  ==============  =========
'''


def get_sample_reader_from_file():
    tmp_file = tempfile.NamedTemporaryFile(suffix='.rst', delete=False)
    tmp_file.write(SAMPLE_TABLES.encode())
    tmp_file.close()

    reader = tableread.SimpleRSTReader(tmp_file.name)
    os.remove(tmp_file.name)
    return reader


readers = [
    get_sample_reader_from_file(),
    tableread.SimpleRSTReader(SAMPLE_TABLES)
]


@attr.s
class FirstTableRow(object):
    name = attr.ib()
    favorite_color = attr.ib()
    favorite_number = attr.ib()


@pytest.fixture
def first_table():
    return [FirstTableRow(*x) for x in [
        ('Bob', 'Red', '3'),
        ('Sue', 'Blue', '5'),
        ('Jim', 'Green', '8')
    ]]


@pytest.mark.parametrize('reader', readers)
def test_open(reader):
    assert reader


@pytest.mark.parametrize('reader', readers)
def test_tables(reader):
    assert reader.tables == ['First Table', 'Second Table']


@pytest.mark.parametrize('reader', readers)
def test_first(reader):
    assert reader.first


@pytest.mark.parametrize('reader', readers)
def test_first_data_matches(reader, first_table):
    for table_row, test_row in zip(reader.first.data, first_table):
        assert attr.asdict(table_row) == attr.asdict(test_row)


@pytest.mark.parametrize('reader', readers)
def test_matches_all_positive(reader):
    match = reader.first.matches_all(name='Bob', favorite_color='Red')
    assert len(match) == 1


@pytest.mark.parametrize('reader', readers)
def test_matches_all_negative(reader):
    match = reader.first.matches_all(name='Greg', favorite_color='Cyan')
    assert not match


@pytest.mark.parametrize('reader', readers)
def test_exclude_by(reader):
    match = reader.first.exclude_by(name='Bob')
    assert len(match) == 2
    for entry in match:
        assert entry.name != 'Bob'


@pytest.mark.parametrize('reader', readers)
def test_get_field(reader):
    table = reader['Second Table']
    fields = table.get_fields('order_from_sun')
    assert [field_value == row.order_from_sun for field_value, row in zip(fields, table)]


@pytest.mark.parametrize('reader', readers)
def test_spillover_last_col(reader):
    pluto = reader['Second Table'].matches_all(planet='Pluto')[0]
    assert pluto.is_planet == 'Forever Yes'


def test_non_existent_file_errors_appropriately():
    with pytest.raises(AssertionError):
        tableread.SimpleRSTReader('./not/a/valid/path/to/file.rst')
