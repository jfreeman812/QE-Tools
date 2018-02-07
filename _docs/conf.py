import os

import sphinx_rtd_theme

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinx.ext.todo',
              'sphinx.ext.coverage', 'sphinx.ext.ifconfig',
              'sphinx.ext.viewcode', 'sphinx.ext.githubpages']

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
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '_docs']

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


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'python': ('https://docs.python.org/3/', None)}
