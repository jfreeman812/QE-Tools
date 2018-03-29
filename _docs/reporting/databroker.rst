Data Broker Endpoint
====================

The Coverage Data Broker supports QE teams to push coverage data to the QE Coverage Dashboard. It takes in raw test coverage entries in list form, does any necessary formatting, and passes them on to the dashboard data collector endpoint.

Input Specifications
--------------------

The URL to POST the data is ``https://qetools.rax.io/coverage/<environment>``. Posted data should be a list of JSON dictionaries, and each entry will be validated to meet the following specifications:

Data in both environments, ``staging`` and ``production``, is validated for the below keys and contents.

Metric Attribute Keys
~~~~~~~~~~~~~~~~~~~~~

Each of these keys are required, and each must match with a value from the relevant table in the :doc:`Coverage Metrics Schema<../../reporting/qe_coverage/coverage>`.

- Execution Method
- Interface Type
- Polarity
- Status
- Suite
- Priority

Test-Specific Keys
~~~~~~~~~~~~~~~~~~

Each of these keys are required.

- Product Hierarchy OR Product (Product is deprecated and may be removed in a future release. Entry must match format ``<Team>::<Product>``)
- Test Name
- Categories

Ticket Keys
~~~~~~~~~~~

These optional keys may be provided to link a test to related work tickets.

- Tickets (a master list of **all** linked tickets)
- quarantined (list of tickets related to a quarantined tag)
- needs work (list of tickets related to a needs-work tag)
- pending (list of tickets related to a pending tag)
- not yet implemented (list of tickets related to a not-yet-implemented tag)

Production-Specific Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Data posted to ``production`` is also validated to ensure each entry has a Product Hierarchy that is on the allowed :doc:`Product Hierarchy Whitelist<../../data_broker/data/whitelist>`.

Output Specifications
---------------------

In addition to the input data, the output will also include the data-collector specific formatting and an ``upload_id`` key that helps identify the set of data uploaded when searching, and tags the data with a unix timestamp.
