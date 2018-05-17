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


Adding New Packages
-------------------

For a new package to be published to Artifactory, a few additional steps must be taken.
Ideally, these steps would be completed before the initial Pull Request is merged into master so that the first version is published automatically.

    * Submit a Pull Request to https://github.rackspace.com/rsi/deploy-answers-artifactory

      * For a python package, update the ``answers/repos/python.yml`` file.
        Copy an existing entry for another QE-Tools package and change the name.
        Make sure to add it in proper alphabetical order.
      * Post a message in ``#rsi-artifacts`` on Slack when the Pull Request has been submitted.

    * Add the package to the ``.pypirc`` on the QE-Tools Jenkins server (reach out on the ``#qe-tools`` channel for help if/as needed).

      * SSH onto the QE-Tools Jenkins Box (currently ``qetools.rax.io``)
      * Switch to the Jenkins user (``sudo su - jenkins``)
      * Create a backup of the PyPI RC file (``cp .pypirc .pypirc.previous``)
      * Add a section for the library, and ensure that the ``username`` and ``password`` remain the same as all the other sections.
        The ``repository`` value in the new section should be
        ``https://artifacts.rackspace.net/artifactory/api/pypi/<NAME FROM deploy-answers-artifactory PULL REQUEST>``
      * Add the new section name to the ``index-servers`` list at the top of the file.

.. warning::

    THE .pypirc  FILE IS NOT IN VERSION CONTROL!!!

.. note::

    If the ``QE-Tools`` Pull Request is merged before the ``deploy-answers-artifactory`` Pull Request,
    request that the updater be manually run in ``#qe-tools`` on Slack once the later is merged.

.. note::

    The current QE-Tools Jenkins box is in the RBA Operations Environment and requires specific LDAP credentials.
    If you do not currently have these permissions, please reach out on the ``#qe-tools`` slack channel to see if a current member of QE-Tools can provide assistance.
