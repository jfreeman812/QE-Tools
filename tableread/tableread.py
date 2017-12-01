import os
from collections import namedtuple, OrderedDict
from itertools import filterfalse
from operator import attrgetter


def _safe_name(name):
    return name.replace(' ', '_').replace('.', '_').lower()


def get_specific_attr_matcher(key, value):
    return lambda x: getattr(x, key).lower() == value.lower()


class BaseRSTDataObject(object):
    column_divider = '  '
    header_divider = '='
    # The full set of potential ReStructuredText section markers is sourced from
    # http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections
    header_markers = set('!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~')
    comment_char = '#'
    data_format = None

    def __init__(self):
        self.data = self.data_format()

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        yield from self.data

    def __getitem__(self, key):
        return self.data[key]

    def _clean_split(self, row):
        return [x.strip() for x in row.split(self.column_divider)]

    def _is_divider_row(self, row):
        if not row.startswith(self.header_divider):
            return False
        return self.header_divider in row and \
            set(row) <= {self.column_divider, self.header_divider, ' '}


class SimpleRSTTable(BaseRSTDataObject):
    data_format = list

    def __init__(self, header, rows, column_spans):
        super().__init__()
        self._header = header
        self._rows = rows
        self._column_spans = column_spans
        self._build_data()

    @classmethod
    def from_data(cls, data):
        table = cls.__new__(cls)
        table.data = list(data)
        return table

    def stop_checker(self, row):
        return self._is_divider_row(row)

    def _row_splitter(self, row):
        assert self._column_spans, 'Column spans not defined!'
        words = []
        for count, span in enumerate(self._column_spans, start=1):
            # Since reStructuredText allows the last column to extend beyond the border, the reader
            # should set the final word as the last span rather than terminating based on the
            # length of the border.
            if count == len(self._column_spans):
                word = row
            else:
                word, row = row[:span], row[span + len(self.column_divider):]
            words.append(word.strip().replace('..', ''))
        return words

    def _build_data(self):
        Row = namedtuple('Row', [_safe_name(x) for x in self._row_splitter(self._header)])
        self.fields = Row._fields
        for row in self._rows:
            if self.stop_checker(row):
                break
            row = row.split(' {} '.format(self.comment_char))[0]
            if row.count(self.column_divider):
                row = self._row_splitter(row)
                message = "Row '{}' does not match field list '{}' length."
                assert len(row) == len(self.fields), message.format(row, self.fields)
                self.data.append(Row(*row))

    def _filter_data(self, data, filter_kwargs, filter_func):
        filters = [v if callable(v) else get_specific_attr_matcher(k, v)
                   for k, v in filter_kwargs.items()]
        data = filter_func(lambda x: all(f(x) for f in filters), data)
        return self.__class__.from_data(data)

    def matches_all(self, **kwargs):
        '''
        Given a set of key/value filters,
        returns a new TableRead object with the filtered data, that can be iterated over.
        Kwarg values may be a simple value (str, int) or a function that returns a boolean.
        '''
        return self._filter_data(self.data, kwargs, filter)

    def exclude_by(self, **kwargs):
        '''
        Given a set of key/value filters,
        returns a new TableRead object without the matching data, that can be iterated over.
        Kwarg values may be a simple value (str, int) or a function that returns a boolean.
        '''
        return self._filter_data(self.data, kwargs, filterfalse)

    def get_fields(self, *fields):
        '''
        Given a set of fields, returns a list of those field values from each entry.
        A single field will return a list of values,
        Multiple fields will return a list of tuples of values.
        '''
        return list(map(attrgetter(*fields), self.data))


class SimpleRSTReader(BaseRSTDataObject):
    data_format = OrderedDict

    def __init__(self, file_path):
        super().__init__()
        assert os.path.exists(file_path), 'File not found: {}'.format(file_path)
        self._parse(file_path)

    @property
    def first(self):
        return list(self.data.values())[0]

    def _is_header_underline(self, row):
        return any((set(row) == set(x) for x in self.header_markers))

    def _table_name(self, section_header):
        section_header = section_header or 'Default'
        if section_header not in self.data.keys():
            return section_header
        name_number = 2
        while True:
            name = '{}_{}'.format(section_header, name_number)
            if name not in self.data.keys():
                return name
            name_number += 1

    def _parse(self, file_path):
        # readlines() does not strip the '\n' from the end of each line, so we use splitlines
        text_lines = open(file_path, 'r').read().splitlines()
        section_header_cursor = None
        i = 0
        while i < len(text_lines) - 1:
            if self._is_header_underline(text_lines[i + 1]):
                section_header_cursor = text_lines[i]
                # skip past the section header AND the underline row
                i += 2
                continue
            if self._is_divider_row(text_lines[i]):
                header, rows, column_spans = self._get_header_and_rows(text_lines[i:])
                table_name = self._table_name(section_header_cursor)
                self.data[table_name] = SimpleRSTTable(header, rows, column_spans)
                # The extra 4 rows 'skipped' are for the three divider rows and the header
                i += len(rows) + 4
            i += 1

    def _get_header_and_rows(self, text_lines):
        header, rows = None, None
        # find the header
        for i in range(len(text_lines)):
            if self._is_divider_row(text_lines[i]):
                assert text_lines[i] == text_lines[i + 2], 'Column divider rows do not match!'
                header, rows = text_lines[i + 1], text_lines[i + 3:]
                column_spans = [len(x) for x in self._clean_split(text_lines[i])]
                break
        # truncate remaining rows to just table contents
        for i in range(len(rows)):
            if self._is_divider_row(rows[i]):
                rows = rows[:i]
                break
        return header, rows, column_spans

    @property
    def tables(self):
        return list(self.data.keys())
