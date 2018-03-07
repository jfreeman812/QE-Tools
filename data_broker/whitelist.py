from os import path

from tableread import SimpleRSTReader


WHITELIST_PATH = ''


class Whitelist(object):
    whitelist_path = 'data/whitelist.rst'
    ph_separator = '::'

    def __init__(self):
        full_path = path.join(path.dirname(path.abspath(__file__)), self.whitelist_path)
        whitelist_table = SimpleRSTReader(full_path).first
        self.allowed_hierarchies = {self._form_hierarchies(row) for row in whitelist_table}

    def _form_hierarchies(self, row):
        return self.ph_separator.join([row.team, row.product])

    def get_disallowed(self, hierarchies_to_check):
        return set(hierarchies_to_check) - self.allowed_hierarchies
