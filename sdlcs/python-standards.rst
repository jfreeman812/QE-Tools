Python Coding Standards and Recommendations
===========================================

We recommend using the following coding standards
to keep all QE Python projects consistent.
The recommendations are in place to provide examples
and guidelines that others in QE currently practice.
If the team has no strong opinions
or experience otherwise,
they should default to the recommendations.


Coding Standards
----------------

Code should be written not only to be executed by a machine
but also to be read and maintained.
Thus, the purpose of coding standards
is not to impede the development process of individual developers,
but to help ensure that the code meets a minimum standard of readability.

We follow the PEP-8_ coding standard,
and highly recommend that any other
QE repositories do the same.

Outside of ``pep8``, we recommend the following additional standards:

* Names should be descriptive.
  With the exception of loops, generator expressions, and comprehensions,
  there should never be single letter variable/class/etc names in the code.
* The maximum recommend line width is 100 characters.
* Always use spaces, never tabs.
* Do not leave trailing white space or trailing blank lines.
* Comment code sections that are
  not readily apparent in their purpose.
* Keep methods small and atomic.
* Keep object oriented principles in mind
  (inheritance, encapsulation, etc.).
* Delete dead code.
  All teams should be using version control
  that lets them go back and retrieve it if needed.
* Don't add speculative
  or "will need this soon" code.
  Such code should be added
  along with the code that will use it,
  otherwise it is just dead code.
* Abstract code where possible.
* Look for patterns
  and create a generic method.
* Use external mechanisms for setting parameters
  (config files, databases, etc.).
* Create and use constants
  for strings and values that don’t change.
* Don't hard-code test data.
* Follow the DRY_ principle.
* Raise exceptions,
  don't return error code values.


Naming Test Data
~~~~~~~~~~~~~~~~

Tests which create/update/delete named entities
in any system-in-test should create names:

* That start with "qe_test" when the data is ephemeral in nature
* contain a timestamp with sub-second resolution
* Additional information *can* be added to the name
  to help with traceability
  and minimizing potential parallel test-execution collisions.

By ensuring all created entities share a common prefix,
test data is easily identifiable,
easing automated or manual test data cleanup.
By including a timestamp on all created entities 
old test data is easily identifiable.


Recommendations and Best Practices
----------------------------------

It is recommended, but not required to follow the following guidelines and suggestions:

* The use of a virtual environment manager.
  `Virtualenv`_ is recommended and commonly used.

* Doc Strings on public functions and methods.
  The Google `napolean documentation standard`_
  is recommended and commonly used.

* The use of code linters and validators:

  * ``flake8`` - basic PEP-8 compliance checking.
  * ``flake8-builtins`` - finds overloaded names of built-ins.
  * ``flake8-comprehensions`` - finds simplifications for generators / comphrehensions.
  * ``flake8-docstrings`` - finds undocumented code.
  * ``flake8-quotes`` - finds inconsistent use of quotes, however you configure this.
  * ``flake8-tuple`` - finds potentially subtle single tuples ``abc,``
  * ``pep8-naming`` - finds inconsistent class, variable, etc. naming.

.. _napolean documentation standard: http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
.. _Virtualenv: https://virtualenv.pypa.io/en/stable/
.. _DRY: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself
.. _PEP-8: https://www.python.org/dev/peps/pep-0008/
