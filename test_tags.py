import os
from collections import namedtuple

Tag = namedtuple('Tag', ['tag', 'purpose', 'report_as', 'description'])


class TestTags(dict):
    def __init__(self, file_name):
        assert os.path.exists(file_name), \
            'Missing tag markdown file at %s' % file_name

        self.groups = dict()
        self.report_names = dict()
        self.group_default = dict()

        text = open(file_name, 'r').read()
        data = text.split('\n---', 1)[1]
        for row in data.splitlines()[1:]:
            if row.count('|'):
                row_data = [x.strip() for x in row.split('|')[:4]]
                tag = Tag(*row_data)
                if tag.tag.startswith('---'):
                    continue
                if tag.tag == '<blank>':
                    self.group_default[tag.purpose] = tag.report_as
                    continue
                assert tag.tag not in self, 'Tag %s is defined twice' % tag.tag
                self[tag.tag] = tag
                self.groups.setdefault(tag.purpose, set()).add(tag.tag)
                self.report_names[tag.tag] = tag.report_as

    @staticmethod
    def is_group_name_reportable(group_name):
        '''Should the given group name be part of coverage reports.'''
        return not group_name.startswith('-')

    def report_groups(self):
        '''Return the list of group names to be part of coverage reports.'''
        return filter(self.is_group_name_reportable, self.groups)


if __name__ == '__main__':
    from pprint import pprint
    tags = TestTags('tags.md')

    print('Tag groups:')
    for k, v in sorted(tags.groups.items()):
        print('Group {} contains: {}'.format(k, ', '.join(v)))
    print()
    print()
    print('How tags are reported:')
    for k, v in sorted(tags.report_names.items()):
        group_name = tags[k].purpose
        if not tags.is_group_name_reportable(group_name):
            print('{} is not a reported tag (part of {})'.format(k, group_name))
            continue
        print("{} is reported as: '{}' (part of {})".format(k, v, group_name))
    print()
    print()
    print('Group Default values:')
    for k, v in tags.group_default.items():
        print('Default for {} is: {}'.format(k, v))
    print()
    print()
    print('Tag details:')
    for t in tags.values():
        pprint(t)
