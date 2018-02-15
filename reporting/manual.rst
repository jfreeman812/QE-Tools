Manual Reporting
================

Tagging the Data
----------------

Tagging and tracking the attributes for the coverage report are outside the scope of this document.

Sending the Data
----------------

To send data separate from the provided tools, a data broker has been created that allows data easily to be sent to the reporting tool. The data broker provides Swagger documentation at https://qetools.rax.io/coverage/doc/ and the data can be posted to https://qetools.rax.io/coverage/staging/.

cURL
~~~~

An example cURL call for posting data to the data broker is::

    curl -X POST -H "Content-Type: application/json" -H "Accept: application/json" -d @/path/to/coverage.json https://qetools.rax.io/coverage/staging/

The ``-d`` parameter for ``curl`` allows for a file path to be provided when prefixed with an at-sign to make the process easier as well.


httpie
~~~~~~

An example call with ``httpie`` (docs_) is::

    httpie https://qetoos.rax.io/coverage/staging/ < /path/to/coverage.json

Reviewing the Reports
---------------------

When sending data to the data broker, a JSON object is returned, when successful, that provides a link to the reporting tool in the ``url`` key, filtered to show all the data uploaded from the same host. This allows the end user to confirm that the data was successfully uploaded. There is a lag between uploading and data appearing in the reporting tool so allow up to five minutes for the data to appear.

.. _docs: http://httpie.org
