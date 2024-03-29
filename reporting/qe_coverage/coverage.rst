.. sectnum::

Coverage Metrics Schema
=======================

This document breaks down the schema that is required for reporting on the QE Coverage Metrics. For an overview of QE Coverage Metrics, as well as information about available tooling, visit the QE Coverage Metrics :doc:`main page<../../_docs/reporting/README>`.

Metrics Attributes
------------------
Within the available coverage data, the following attributes have been identified as significant and useful for reporting:

===================  =================================================================================
Attribute            Description
===================  =================================================================================
Product_             The name of the product to which a test applies.
Projects_             The name of any project(s) associated with the test.
`Test Name`_         A brief, descriptive name for the test.
`Interface Type`_    Designation for the interface being targeted by the test (e.g., API).
Polarity_            Designates whether a test targets normal or abnormal behavior (happy vs sad path)
Priority_            The importance assigned to a test.
Suite_               Designates the test suite, if any, to which the test belongs.
Status_              The operational status of the test.
`Execution Method`_  If the test is run manually or via automation.
Categories_          Hierarchical levels of functional groups into which tests can be categorized
Tickets_             Any tickets associated with a given test.
===================  =================================================================================

Attribute Usage
---------------
The data for the coverage metrics can be collected through a number of ways. The following tables break down the acceptable values for each group listed above:

Prescriptive Tags
~~~~~~~~~~~~~~~~~
The coverage attributes are associated with tests by applying tags in the source files that contain the tests. Utility scripts are available to extract the tags out of the source files. Once the data is collected, the same scripts can transmit that data to our metrics platform for publishing. This tool chain only works if the tags are applied correctly and consistently.

This section provides the valid tag values which may be applied to the source files for each of the coverage attributes. For each coverage attribute, the tables have the following columns:

* Tag – The tag column defines the exact string which must be used in conjunction with the appropriate tagging mechanism in the source file in order to apply that attribute value to the test.

  * For Gherkin-based tests, the tags are applied via the syntax ``@<Tag>`` where the ``<Tag>`` is the value defined in the Tag column. Tags may span across multiple lines and logically-grouped tags should appear together (e.g., adding a Status_ tag and the associated Tickets_)

  * For Unittest and CAFE-based tests, the tags are applied via the syntax ``@tags("<Tag 1>", "<Tag 2>", ...)``, where the quoted tag values are the values defined in the Tag column. Tags must all be contained in the same decorator.

* Report As – The 'report as' column defines the resulting value which will be written to the coverage metrics when that tag is encountered in a source file.

* Description – The description provides relevant information about the tag.

If a particular definition table has a row with a blank entry in the Tag column, that row represents a default value which will be assumed for that attribute if no tag for that attribute is present in the source file.

NOTE: With the exception of Tickets_ and Projects_ only one tag within each attribute can be applied at one time. If there is no default value, then a tag for that attribute must be applied.

Interface Type
^^^^^^^^^^^^^^

===========  ====================  ===============================================================================
Tag          Report As             Description
===========  ====================  ===============================================================================
api          api                   Test that executes against an API.
gui          gui                   Test that executes against a GUI.
..           ``<argument_value>``  The default value is provided as a command-line argument to the coverage tools.
===========  ====================  ===============================================================================

**Note:** Since a particular test framework often targets a single interface type, the tests are often segregated by interface type as well. In such cases, it is easier to specify the interface type at the time of coverage collection rather than applying the same tag over and over again to hundreds of tests.

Polarity
^^^^^^^^

===========  ===================  ====================================================
Tag          Report As            Description
===========  ===================  ====================================================
positive     positive             Test is a positive/happy path/down-the-fairway case.
negative     negative             Test is a negative/sad path/in-the-weeds case.
===========  ===================  ====================================================

Priority
^^^^^^^^

===========  ===================  ==========================================
Tag          Report As            Description
===========  ===================  ==========================================
p0           high                 Most important test(s) to implement first.
p1           medium               Medium priority.
p2           low                  Low priority.
..           medium               Medium priority.
===========  ===================  ==========================================

**Note:** Per agreement with leadership, priority is not required for tests that existed before a team adopts this standard.

Suite
^^^^^

===========  ===================  ======================================================================================
Tag          Report As            Description
===========  ===================  ======================================================================================
deploy       deploy               Build verification test / quick test to validate successful deployment.
smoke        smoke                Checks for basic functionality. Smoke tests should take less than 10 minutes in total.
load         performance          Test is designed to stress the application.
integration  integration          Test exercises multiple applications and not just one component
security     security             Test is a security test
..           all                  Test run during a normal test execution without restrictions.
===========  ===================  ======================================================================================

Status
^^^^^^

===========  ===================  =======================================================================================
Tag          Report As            Description
===========  ===================  =======================================================================================
nyi          not yet implemented  Test has been targeted for implementation, but hasn't yet been written.
not-tested   pending              Test is ready, but the service / subject is not ready.
needs-work   needs work           Test is offline due to a problem with the test; QE needs to fix.
quarantined  quarantined          Test is offline due to bug in application / system / etc. Outside of QE's scope to fix.
unstable     unstable             Test is online but the test is not consistently passing.
..           operational          Test is online and being executed.
===========  ===================  =======================================================================================

**Note:** For any non-default status tag, the tag should be followed by one or more Ticket tags (see: Tickets_) that are tracking the work needed to bring the test into operational state. The Ticket tags must follow immediately after the non-default status tag until any non-Ticket tag (or end of tags). For example:

.. code:: Gherkin

    Gherkin
    -------
    @quarantined @JIRA-1234
    @needs-work @JIRA-5678 @JIRA-4321


    Unittest/OpenCAFE
    -----------------
    @tags( ..., "quarantined", "JIRA-1234", ...)
    @tags( ..., "needs-work", "JIRA-5678", "JIRA-4321", ...)

The quarantined tag can be particularly useful as it provides a mechanism to exclude known failures from a test run, thereby making it easier to isolate new test failures from recurring, known test failures. Similarly, the needs-work tag can be a convenient method to take a test which needs repair work offline while it waits for the repair.

Execution Method
^^^^^^^^^^^^^^^^

===========  ===================  =====================================================
Tag          Report As            Description
===========  ===================  =====================================================
manual       manual               Test is executed manually and recorded for reporting.
automated    automated            Test is executed though the testing framework.
..           automated            Test is executed though the testing framework.
===========  ===================  =====================================================


Structured Tags
~~~~~~~~~~~~~~~

The following tags, unlike the previous section, do not have a predefined list of acceptable values but instead have a specific structure for identifying the tag as a attribute. The free form information used in the structure provides the meaningful data specific to the test.

.. _Projects:

:Attribute: Projects
:Format: ``project:<project_id>``
:Description:
    The project designation allows work to be tracked for a particular project. While these tests can outlast a project, the tags allow for a historical record to the rationale for the test. Since a test can be relevant for multiple projects, a test may have multiple project tags.

.. _Categories:

:Attribute: Categories
:Format: ``category:<category_1>:<category_2>:<category_n>``
:Description:
    The categories attribute allows for a hierarchical structure for tests. For example, for testing an automobile, the tests might be organized into ``Engine -> Coolant System -> Radiator``. The categories attribute can be conveyed in two ways. In the first way, the tests can be organized in a directory structure where each directory represents a category and nesting of the directories represents the hierarchy. In the second way, the categories can be applied explicitly to a test via the category tag. This is helpful if a team wants to use their directory structure for some other type of organization other than test category.

    If the category tag is not applied to a test, the coverage tools may extract the categories from the directory structure which holds the test. Regardless of whether the tagging is implicit via the reporting tool or explicit via the category tag, the hierarchy can be as deep as needed and represents a nested group of categories for a test.

.. _Tickets:

:Attribute: Tickets
:Format: ``<Ticket_ID>``
:Description:
    When applicable, any ticket ID associated with a test should be added as a tag.
    Ticket tags fall into two categories, "status" ticket tags and "independent" ticket tags.
    "Status" ticket tags are those which immediately follow a Status_ tag;
    "Independent" ticket tags are all other ticket tags.

    "Independent" ticket tags are *strongly* recommended for any non-trivial test; they link the test back to the issue describing why it was created (traceability).
    "Status" tickets answer the question "Why is this test not operational right now?"

    Note that when a status tag is removed, the "status" ticket tags should remain, as the test's "why it was created" history has additional nuance that we also want traceability for.


Additional Attributes
~~~~~~~~~~~~~~~~~~~~~
The following attributes are populated outside the above tagging mechanism.

.. _Product:

:Attribute: Product
:Description:
    The product name and is provided to the coverage tools.

.. _Test Name:

:Attribute: Test Name
:Description:
    This is the test name captured from the source files. For Gherkin, this is the scenario title. For Unittest/OpenCAFE, this is the function name or the first line of the doc string, if present.

Reporting Specification
-----------------------

The coverage data needs to be reported in a standard format that conforms to the above fields and restrictions. The coverage data must be output in an array of json objects.

Output formatting specifications:

* For the `Prescriptive Tags`_, the key is the attribute name and the value is the value from *Report As*.
* For the Projects_ and Categories_, the key is the attribute name and the value is as follows:

  * For Projects_, the value is the full value after the identifier (``project:``)
  * For Categories_, the value is a list of categories built from splitting on the separator (``:``) after the identifier (``category:``)

* For Tickets_, the key is the Status_ *Report As* value associated with the Tickets_ and the value is the list of Tickets_ *for that status*. In the case where a Ticket ID has no associated Status_, the attribute name `Tickets` is used.

**Note:** it is possible to have multiple tickets associated with a test for multiple statuses. An example is that a ticket tag exists for when the test was created but the test is quarantined due to a later code change and is now quarantined with tickets. This is an acceptable behavior and the json should reflect two ticket lists, one for the pre-existing tags and one for quarantined.

Example JSON Object
~~~~~~~~~~~~~~~~~~~

.. code:: json

        [
            {
                "Product": "Script Management",
                "Projects": [],
                "Test Name": "Add a Module",
                "Interface Type": "api",
                "Polarity": "positive",
                "Priority": "p0",
                "Suite": "integration",
                "Categories": [
                    "modules",
                    "commands"
                ],
                "Status": "operational",
                "Execution Method": "automated",
                "Tickets": ["JIRA-3344"]
            },
            {
                "Product": "Script Management",
                "Projects": [],
                "Test Name": "Missing Fields",
                "Interface Type": "api",
                "Polarity": "negative",
                "Priority": "p1",
                "Suite": "integration",
                "Categories": [
                    "modules",
                    "commands"
                ],
                "Status": "quarantined",
                "Execution Method": "automated",
                "quarantined": ["JIRA-1234", "JIRA-4321"]
            }
        ]
