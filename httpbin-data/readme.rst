httpbin-data: HTTP Request & Response Service
=============================================

This is an extention of httpbin <http://httpbin.org/> to allow for testing and verifying CRUD operations

Additional Endpoints
--------------------

==================================  ======  ==========================================================================
Endpoint                            Method  Description
----------------------------------  ------  --------------------------------------------------------------------------
`/data-check`                       GET     Return all data check group.
`/data-check`                       POST    Create data check group; requires the key `group_name`.
`/data-check/:group_name`           DELETE  Delete a data check group.
`/data-check/:group_name`           GET     Return all data sent to a data group via POST and PUT.
`/data-check/:group_name`           POST    Accepts data and returns a data dictionary with the `:data_id` as the key.
`/data-check/:group_name/:data_id`  GET     Get the data dictionary for the given `data_id`.
`/data-check/:group_name/:data_id`  PUT     Update the data dictionary for the given `data_id`
`/data-check/:group_name/:data_id`  DELETE  Delete the data dictionary for the given `data_id`
`/counter/:counter_name`            GET     Return the hit count for counter name
`/counter/:counter_name`            PUT     Increment hit count for counter name and return value
`/counter/:counter_name`             DELETE  Delete the counter (reset to 0)
==================================  ======  ==========================================================================

Description
-----------

The data dictionary is formatted just like `/post` and `/put` do, except that the data dictionary is nested into another dictionary where the `:data_id` is the key.

Examples
--------

$ curl -X POST -d '{"group_name": "test"}' http://localhost:5000/data-check/
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    {
      "group_name": "test"
    }

$ curl http://localhost:5000/data-check/
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    [
      "test"
    ]

$ curl -X POST -d "a=b" -d "c=d" http://localhost:5000/data-check/test/
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    {
      "0d411eac-5f00-4d41-bc2e-7d6745e01e29": {
        "args": {},
        "data": "",
        "files": {},
        "form": {
          "a": "b",
          "c": "d"
        },
        "headers": {
          "Accept": "*/*",
          "Content-Length": "7",
          "Content-Type": "application/x-www-form-urlencoded",
          "Host": "localhost:5000",
          "User-Agent": "curl/7.51.0"
        },
        "json": null,
        "origin": "127.0.0.1",
        "url": "http://localhost:5000/data-check/test/"
      }
    }

$ curl -X PUT -d '{"c": "d"}' -H "Content-Type: application/json" http://localhost:5000/data-check/test/0d411eac-5f00-4d41-bc2e-7d6745e01e29
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    {
      "args": {},
      "data": "{\"c\": \"d\"}",
      "files": {},
      "form": {},
      "headers": {
        "Accept": "*/*",
        "Content-Length": "10",
        "Content-Type": "application/json",
        "Host": "localhost:5000",
        "User-Agent": "curl/7.51.0"
      },
      "json": {
        "c": "d"
      },
      "origin": "127.0.0.1",
      "url": "http://localhost:5000/data-check/test/e976cbfc-d9f3-4adc-bc3d-43d075b0ffef"
    }

$ curl -X DELETE http://localhost:5000/data-check/test/0d411eac-5f00-4d41-bc2e-7d6745e01e29
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    {
      "message": "0d411eac-5f00-4d41-bc2e-7d6745e01e29 deleted successfully"
    }


$ curl -X DELETE http://localhost:5000/data-check/test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    {
      "message": "test deleted successfully"
    }


$ curl http://localhost:5000/counter/test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::
    {
      "test": 0
    }


$ curl -X PUT http://localhost:5000/counter/test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::
    {
      "test": 1
    }


$ curl -X DELETE http://localhost:5000/counter/test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::
    {
      "message": "test deleted!"
    }
