import os
from collections import OrderedDict
try:
    from itertools import filterfalse
except ImportError:
    from itertools import ifilterfalse as filterfalse
from operator import attrgetter

import attr


def _safe_name(name):
    return name.replace(' ', '_').replace('.', '_').lower()


def get_specific_attr_matcher(key, value):
    return lambda x: getattr(x, key).lower() == value.lower()


class BaseRSTDataObject(object):
    column_divider = '  '
    header_divider = '='
    # The full set of potential ReStructuredText section markers is sourced from
    # http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections
    header_markers = set(r'!"#$%&\'()*+,-./:;<=>?@[]^_`{|}~')
    col_default_separator = '='
    comment_char = '#'
    data_format = None

    def __init__(self):
        self.data = self.data_format()

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for data in self.data:
            yield data

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
        super(SimpleRSTTable, self).__init__()
        self._header = header
        self._rows = rows
        self._column_spans = column_spans
        self._build_data()

    @classmethod
    def from_data(cls, data):
        table = cls.__new__(cls)
        table.data = list(data)
        return table

    def _stop_checker(self, row):
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

    def _set_header_names_and_defaults(self, fields):
        name_sets = [x.split(self.col_default_separator, 1) for x in fields]
        self.fields = [_safe_name(x[0].strip()) for x in name_sets]
        self.defaults = [x[1].strip() if len(x) > 1 else '' for x in name_sets]

    def _build_data(self):
        self._set_header_names_and_defaults(self._row_splitter(self._header))
        row_class = attr.make_class('Row', self.fields, hash=True)
        for row in self._rows:
            if self._stop_checker(row):
                break
            if '\t' in row:
                raise TabError('Tabs are not supported in tables - use spaces only!')
            row = row.split(' {} '.format(self.comment_char))[0]
            if row.count(self.column_divider):
                row = self._row_splitter(row)
                message = "Row '{}' does not match field list '{}' length."
                assert len(row) == len(self.fields), message.format(row, self.fields)
                row_data = (
                    value if value else default for default, value in zip(self.defaults, row)
                )
                self.data.append(row_class(*row_data))

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

    def __init__(self, rst_source):
        '''
        Determine from where to parse RST content and then parse it.

        Args:
            rst_source (str): The source of the RST content to parse. This can either be a
                file path with a ``.rst`` extension, or a string containing the RST content.
        '''
        super(SimpleRSTReader, self).__init__()
        rst_string = rst_source
        if rst_source.lower().endswith('.rst'):
            rst_string = self._read_file(rst_source)
        self._parse(rst_string)
        assert self.data, 'No tables could be parsed from the RST source.'

    @staticmethod
    def _read_file(file_path):
        assert os.path.exists(file_path), 'File not found: {}'.format(file_path)
        with open(file_path, 'r') as rst_fo:
            return rst_fo.read()

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

    def _parse(self, rst_string):
        text_lines = rst_string.split('\n')
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
