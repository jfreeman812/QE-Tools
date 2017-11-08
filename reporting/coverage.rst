Coverage Metrics
================

Rationale
---------
In order to communicate clearly across teams, it is important to ensure that a common nomenclature is established. As we work to have a common nomenclature for coverage data and results metrics, the following definitions have been established:

Metrics Fields
--------------
Within the available coverage data, the following groups have been identified as significant and useful for reporting:


================  ============================================================================
Group             Description
================  ============================================================================
Product           The name of the product.
Project           The name of any project associated with the test that is being created.
Test Name         A brief, descriptive name for the test.
Interface Type    Designation for the interface being targeted by the test.
Polarity          Designation of a test for expected outcome (happy vs sad path)
Priority          The importance assigned to a test.
Suite             Designates the test suite, if any, to which the test belongs.
Categories        Hierarchical levels of functional groups into which tests can be categorized
Status            The operational status of the test.
Execution Method  If the test is run manually or via automation.
================  ============================================================================

Data Collection
---------------
The data for the coverage metrics can be collected through a number of ways. The following tables break down the acceptable values for each group listed above:

Prescriptive Tagging
~~~~~~~~~~~~~~~~~~~~
The following groups are collected by adding predefined tags to the tests or tests groups. For tables that have a blank for **Tag**, that represents a default value if no tag is present.

===========  ===================  =======================================================================================
Status
-------------------------------------------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  =======================================================================================
nyi          not yet implemented  Test is a skeleton for generating data on scoping.
not-tested   pending              Test is ready, but the service / subject is not ready.
needs-work   needs work           Test is offline due to a problem with the test; QE needs to fix.
quarantined  quarantined          Test is offline due to bug in application / system / etc. Outside of QE's scope to fix.
..           operational          Test is online and being executed.
===========  ===================  =======================================================================================


===========  ===================  =======================================================================================
Suite
-------------------------------------------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  =======================================================================================
deploy       smoke                Build verification test / quick test to validate successful deployment.
smoke        unit                 Checks for basic functionality. Smoke tests should take less than 10 minutes in total.
load         performance          Test is designed to stress the application.
solo         solo                 Test that cannot be run in parallel with any other tests.
integration  integration          Test exercises multiple applications and not just one component
security     security             Test is a security test
..           all                  Test run during a normal test execution without restrictions.
===========  ===================  =======================================================================================


===========  ===================  =======================================================================================
Priority
-------------------------------------------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  =======================================================================================
p0           high                 Most important test(s) to implement first.
p1           medium               Medium priority.
p2           low                  Low priority.
..           medium               Medium priority.
===========  ===================  =======================================================================================


===========  ===================  =======================================================================================
Polarity
-------------------------------------------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  =======================================================================================
positive     positive             Test is a positive/happy path/down-the-fairway case.
negative     negative             Test is a negative/sad path/in-the-weeds case.
===========  ===================  =======================================================================================
Note: Per agreement with leadership, priority is not required for tests that existed before a team adopts this standard.

===========  ===================  =======================================================================================
Execution Method
-------------------------------------------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  =======================================================================================
manual       automated            Test is executed manually and recorded for reporting.
automated    automated            Test is executed though the testing framework.
..           automated            Test is executed though the testing framework.
===========  ===================  =======================================================================================


===========  ===================  =======================================================================================
Interface Type
-------------------------------------------------------------------------------------------------------------------------
Tag          Report As            Description
===========  ===================  =======================================================================================
api          api                  Test that executes against an API.
gui          gui                  Test that executes against a GUI.
..           <cli_argument>       The default value is provided as a command-line argument to the coverage tools.
===========  ===================  =======================================================================================


Structured Tags
~~~~~~~~~~~~~~~
The following tags have a structure for identifying the tag as a group, but the information contained in the tag is at the discretion of the user.

:Group: Project
:Format: ``project:<project_id>``
:Description: The project designation allows work to be tracked for a particular project. While these tags can outlast a project, the tags allow for a historical record to the rationale for the test.

..

:Group: Categories
:Format: ``category:<category_1>:<category_2>:<category_n>``
:Description: The categories tag allows for a category hierarchy to be establish independent of directory structure (the default behavior for Gherkin-based tools). The hierarchy can be as deep as needed and represents a nested group of categories for a test.

Additional Groups
~~~~~~~~~~~~~~~~~
The following groups are populated outside of tagging.

:Group: Product
:Description: The product name and is provided to the coverage tools.

..

:Group: Test Name
:Description: This is the test name captured from the files. For Gherkin, this is the scenario title. For OpenCAFE, this is the function name.

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
        "execution": "automated"
    }
    ],
    "report_date": "2016-10-11T22:57:43.511Z"
    }
