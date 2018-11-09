'''Unit Tests for the TableRead SimpleRSTReader.'''

import pytest
import attr

import tableread


@pytest.fixture
def sample_rst_table():
    return tableread.SimpleRSTReader('tests/sample_table.rst')


@attr.s
class FirstTableRow:
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


def test_open(sample_rst_table):
    assert sample_rst_table


def test_tables(sample_rst_table):
    assert sample_rst_table.tables == ['First Table', 'Second Table']


def test_first(sample_rst_table):
    assert sample_rst_table.first


def test_first_data_matches(sample_rst_table, first_table):
    for table_row, test_row in zip(sample_rst_table.first.data, first_table):
        assert attr.asdict(table_row) == attr.asdict(test_row)


def test_matches_all_positive(sample_rst_table):
    match = sample_rst_table.first.matches_all(name='Bob', favorite_color='Red')
    assert len(match) == 1


def test_matches_all_negative(sample_rst_table):
    match = sample_rst_table.first.matches_all(name='Greg', favorite_color='Cyan')
    assert not match


def test_exclude_by(sample_rst_table):
    match = sample_rst_table.first.exclude_by(name='Bob')
    assert len(match) == 2
    for entry in match:
        assert entry.name != 'Bob'


def test_get_field(sample_rst_table):
    table = sample_rst_table['Second Table']
    fields = table.get_fields('order_from_sun')
    assert [field_value == row.order_from_sun for field_value, row in zip(fields, table)]


def test_spillover_last_col(sample_rst_table):
    pluto = sample_rst_table['Second Table'].matches_all(planet='Pluto')[0]
    assert pluto.is_planet == 'Forever Yes'
