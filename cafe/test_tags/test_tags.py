"""
    This will create a dict of TestTags in the variable tags from the markdown
    file ../../tags.md

    Installation:
        repo>pip install .

    Code:
        from cafe.test_tags import tags
"""

import os

TAG_MARKDOWN_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tags.md')


class TestTags(object):
    def __init__(self, tag, purpose, description):
        self.tag = tag.strip()
        self.purpose = purpose.strip().split(',')
        self.description = description.strip()

    @classmethod
    def generate_dict_from_markdown_file(cls):
        assert os.path.exists(TAG_MARKDOWN_FILE), \
            'Missing tag markdown file at %s' % TAG_MARKDOWN_FILE

        ret = {}
        text = open(TAG_MARKDOWN_FILE, 'r').read()
        heading, data = text.split('\n---', 1)
        for row in data.split('\n')[1:]:
            if row.count('|') > 1:
                tag = TestTags(*row.split('|')[:3])
                assert tag.tag not in ret, 'Tag %s was defined twice' % tag.tag
                ret[tag.tag] = tag
        return ret

    def __str__(self):
        return '%s: %s: %s'%(self.tag, self.purpose, self.description)

    def __repr__(self):
        return '%s(tag=%s)'%(self.__class__.__name__, repr(self.tag))


tags = TestTags.generate_dict_from_markdown_file()
