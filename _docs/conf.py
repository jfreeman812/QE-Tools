import os
import sys

import sphinx_rtd_theme

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.todo',
              'sphinx.ext.coverage', 'sphinx.ext.ifconfig',
              'sphinx.ext.viewcode', 'sphinx.ext.githubpages',
              'sphinx.ext.inheritance_diagram',
              ]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

source_suffix = ['.rst']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'QE Tools Documentation'
copyright = '2018, Rackspace Quality Engineering'  # noqa
author = 'Rackspace Quality Engineering'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = ''
# The full version, including alpha/beta/rc tags.
release = ''

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.tox', '*/.tox', '.eggs', '*/.eggs',
                    'README.rst', '*/tests']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
commit_id = os.environ.get('ghprbPullId') or os.environ.get('GIT_COMMIT_ID')
base_url = os.environ.get('ghprbPullLink')
if not base_url:
    owner_name = os.path.splitext(os.environ.get('GIT_ORIGIN_URL').split(':')[1])[0]
    base_url = 'https://github.rackspace.com/{}/tree/{}'.format(owner_name, commit_id)
html_context = {'build_id': commit_id, 'build_url': base_url}

# Next two assignments from:
# https://rackerlabs.github.io/docs-rackspace/tools/rtd-tables.html
# in order to keep the terminology table from having a horizontal scroll bar.

html_static_path = ['_static']

html_context = {
    'css_files': [
        '_static/theme_overrides.css',  # override wide tables in RTD theme
    ],
}


def html_page_context_handler(app, pagename, templatename, context, doctree):
    # The coverage documentation was shared, for an extended period, from the root
    # path in the documentation. This method tells Sphinx to recreate this file in the
    # root to preserve those links.
    if '/coverage' in pagename:
        new_page = pagename.split('/')[-1]
        # Tell Sphinx that this new page should have the same TOC as the old
        app.env.toc_num_entries[new_page] = app.env.toc_num_entries[pagename]
        ctx = app.builder.get_doc_context(new_page, context['body'], context['metatags'])
        # Remove the sourcename to prevent a duplicate source file being copied
        ctx['sourcename'] = None
        app.builder.handle_page(new_page, ctx, event_arg=doctree)


def skip(app, what, name, obj, skip, options):
    if name == '__init__':
        return False
    return skip


def setup(app):
    app.connect('html-page-context', html_page_context_handler)
    app.connect('autodoc-skip-member', skip)
