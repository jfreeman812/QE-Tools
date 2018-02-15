Using Artifactory
=================

Artifactory is a general repository manager that has functionality for providing a caching mirror for PyPI as well as allowing internal projects to be hosted. Libraries uploaded to Artifactory can be installed in one of three ways:

#. Explicitly telling ``pip`` where to find the index via ``pip install -i "https://artifacts.rackspace.net/artifactory/api/pypi/pypi/simple"``
#. Adding Artifactory to pip's configuration file: ``~/.pip/pip.conf``. The config file would contain::

    [global]
    index-url = https://artifacts.rackspace.net/artifactory/api/pypi/pypi/simple

#. Using Artifactory with ``pipenv`` (docs_). The opening section for the ``Pipfile`` in a repository would contain::

    [[source]]

    url = "https://artifacts.rackspace.net/artifactory/api/pypi/pypi/simple"
    verify_ssl = true
    name = "artifactory"

.. _docs: https://docs.pipenv.org
