Coverage Metrics
================

Rationale
---------
In order to communicate test coverage clearly, both within and across our teams, it is important to ensure that a common coverage nomenclature is established. This page documents the common nomenclature used by our teams to collect and communicate our coverage metrics. All test coverage shall be reported using the nomenclature established here.

While allowing us to communicate our coverage, the markup mechanisms defined in this page also allow us to selectively control execution of our tests. Again, it’s important to use common nomenclature so that teams can leverage each other's work in consistent way.

Metrics Fields
--------------
Within the available coverage data, the following attributes have been identified as significant and useful for reporting:


================  =================================================================================
Attribute         Description
================  =================================================================================
Product           The name of the product to which a test applies.
Project           The name of any project associated with the test that is being created.
Test Name         A brief, descriptive name for the test.
Interface Type    Designation for the interface being targeted by the test (e.g., API).
Polarity          Designates whether a test targets normal or abnormal behavior (happy vs sad path)
Priority          The importance assigned to a test.
Suite             Designates the test suite, if any, to which the test belongs.
Status            The operational status of the test.
Execution Method  If the test is run manually or via automation.
Categories        Hierarchical levels of functional groups into which tests can be categorized
JIRAs             Any JIRAs associated with a given test.
================  =================================================================================

Data Collection
---------------
The coverage attributes are associated with tests by applying tags in the source files that contain the tests. Utility scripts are available to extract the tags out of the source files. Once the data is collected, the same scripts can transmit that data to our metrics platform for publishing. This tool chain only works if the tags are applied correctly and consistently.

This section provides the valid tag values which may be applied to the source files for each of the coverage attributes. For each coverage attribute, the tables have the following columns:

* Tag – The tag column defines the exact string which must be used in conjunction with the appropriate tagging mechanism in the source file in order to apply that attribute value to the test. For Gherkin-based tests, the tags are applied via the syntax '@<Tag>' where the <Tag> is the value defined in the Tag column. For CAFE-based tests, the tags are applied via the syntax '@tags("<Tag 1>", "<Tag 2>", ...)', where the quoted tag values are the values defined in the Tag column.
* Report As – The 'report as' column defines the resulting value which will be written to the coverage metrics when that tag is encountered in a source file.
* Description – The description provides relevant information about the tag.

If a particular definition table has a row with a blank entry in the Tag column, that row represents a default value which will be assumed for that attribute if no tag for that attribute is present in the source file.


Prescriptive Tags
~~~~~~~~~~~~~~~~~
The following groups are collected by adding predefined tags to the tests or tests groups. For tables that have a blank for **Tag**, that represents a default value if no tag is present.

===========  ====================  ===============================================================================
Interface Type
------------------------------------------------------------------------------------------------------------------
Tag          Report As             Description
===========  ====================  ===============================================================================
api          api                   Test that executes against an API.
gui          gui                   Test that executes against a GUI.
..           ``<argument_value>``  The default value is provided as a command-line argument to the coverage tools.
===========  ====================  ===============================================================================
Note: Since a particular test framework often targets a single interface type, we often segregate our API or GUI tests from each other. In such cases, it is easier to specify the interface type at the time of coverage collection rather than applying the same tag over and over again to hundreds of tests.


===========  ===================  ====================================================
Polarity
--------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  ====================================================
positive     positive             Test is a positive/happy path/down-the-fairway case.
negative     negative             Test is a negative/sad path/in-the-weeds case.
===========  ===================  ====================================================


===========  ===================  ==========================================
Priority
----------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  ==========================================
p0           high                 Most important test(s) to implement first.
p1           medium               Medium priority.
p2           low                  Low priority.
..           medium               Medium priority.
===========  ===================  ==========================================
Note: Per agreement with leadership, priority is not required for tests that existed before a team adopts this standard.


===========  ===================  ======================================================================================
Suite
------------------------------------------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  ======================================================================================
deploy       smoke                Build verification test / quick test to validate successful deployment.
smoke        unit                 Checks for basic functionality. Smoke tests should take less than 10 minutes in total.
load         performance          Test is designed to stress the application.
solo         solo                 Test that cannot be run in parallel with any other tests.
integration  integration          Test exercises multiple applications and not just one component
security     security             Test is a security test
..           all                  Test run during a normal test execution without restrictions.
===========  ===================  ======================================================================================


===========  ===================  =======================================================================================
Status
-------------------------------------------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  =======================================================================================
nyi          not yet implemented  Test has been targeted for implementation, but hasn't yet been written.
not-tested   pending              Test is ready, but the service / subject is not ready.
needs-work   needs work           Test is offline due to a problem with the test; QE needs to fix.
quarantined  quarantined          Test is offline due to bug in application / system / etc. Outside of QE's scope to fix.
..           operational          Test is online and being executed.
===========  ===================  =======================================================================================
Note: For any non-default status tag, the tag should be followed by one or more JIRA tags (see: JIRAs_) that are tracking the work needed to bring the test into operational state. For example:

.. code::

    Gherkin
    -------
    @quarantined @JIRA-1234
    @needs-work @JIRA-5678 @JIRA-4321


    OpenCAFE
    --------
    @tags("quarantined", "JIRA-1234", "needs-work", "JIRA-5678", "JIRA-4321")

The quarantined tag can be particularly useful as it provides a mechanism to exclude known failures from a test run, thereby making it easier to isolate new test failures from recurring, known test failures. Similarly, the needs-work tag can be a convenient method to take a test which needs repair work offline while it waits for the repair.

===========  ===================  =====================================================
Execution Method
---------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  =====================================================
manual       automated            Test is executed manually and recorded for reporting.
automated    automated            Test is executed though the testing framework.
..           automated            Test is executed though the testing framework.
===========  ===================  =====================================================


Structured Tags
~~~~~~~~~~~~~~~

The following tags, unlike the previous section, do not have a predefined list of acceptable values but instead have a specific structure for identifying the tag as a attribute. The free form information used in the structure provides the meaningful data specific to the test.

:Attribute: Project
:Format: ``project:<project_id>``
:Description: The project designation allows work to be tracked for a particular project. While these tags can outlast a project, the tags allow for a historical record to the rationale for the test.

..

:Attribute: Categories
:Format: ``category:<category_1>:<category_2>:<category_n>``
:Description: The categories tag allows for a category hierarchy to be establish independent of directory structure (the default behavior for Gherkin-based tools). The hierarchy can be as deep as needed and represents a nested group of categories for a test.

.. _JIRAs:

:Attribute: JIRAs
:Format: ``<JIRA_ID>``
:Description: When applicable, any JIRA associated with a test should be added as an independent tag. This allows for tests to be run for specific JIRA(s) as well as a historic record of the reason a test was added to the suite.

Additional Attributes
~~~~~~~~~~~~~~~~~~~~~
The following attributes are populated outside the above tagging mechanism.

:Attribute: Product
:Description: The product name and is provided to the coverage tools.

..

:Attribute: Test Name
:Description: This is the test name captured from the source files. For Gherkin, this is the scenario title. For OpenCAFE, this is the function name.

Coverage Data Reporting Format
------------------------------

The coverage data needs to be reported in a standard format that conforms to the above fields and restrictions. The coverage data must be output in an array of json objects.

Example JSON Object
~~~~~~~~~~~~~~~~~~~

.. code:: json

    {
        "coverage": [
            {
                "product": "Script Management",
                "project": "",
                "test_name": "Add a Module",
                "interface": "api",
                "polarity": "positive",
                "priority": "p0",
                "suite": "integration",
                "categories": [
                    "modules",
                    "commands"
                ],
                "status": "operational",
                "execution": "automated"
            },
            {
                "product": "Script Management",
                "project": "",
                "test_name": "Missing Fields",
                "interface": "api",
                "polarity": "negative",
                "priority": "p1",
                "suite": "integration",
                "categories": [
                    "modules",
                    "commands"
                ],
                "status": "operational",
                "execution": "automated",
                "JIRAs": ["JIRA-1234", "JIRA-4321"]
            }
        ],
        "report_date": "2016-10-11T22:57:43.511Z"
    }
